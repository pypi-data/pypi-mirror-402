A Lightweight and General Data Synchronization Solution
=======================

Data synchronization between different database systems is a common requirement in the big data field. A typical scenario is that the business system uses MySQL for transactions and random queries; the data warehouse uses Hive; the results after ETL are then put into systems such as MySQL, AWS Redshift, etc. for use by BI and reporting tools.

First, let's clarify the requirements and goals:

- Real-time: Non-real-time, offline synchronization, generally T+1, or as fine as hourly granularity
- Scalability: Need to support multiple heterogeneous data sources, such as MySQL, Hive, ElasticSearch, etc.
- Performance requirements: Because it is an offline system, there is no strict requirement for performance, but it is best to be as fast as possible and possible to optimize
- Complexity: Low complexity, few dependencies, easy to use, easy to operate
- Functional requirements: Need to meet full synchronization and incremental data synchronization

## Solution

Data synchronization is not a special problem, it is actually just two operations: read and write. Similar to this is the database backup and restore, many database systems have such tools, such as MySQL's `mysqldump` and `mysqlimport`, MongoDB's `mongodump` and `mongorestore`, etc. These tools generally use special encoding formats for performance and do not consider generality. But a general data synchronization system can be implemented using the same approach.

![pigeon_design.png](./images/pigeon_design.png)

The above picture describes the solution of this article, which is to split the read and write, and transition through CSV files.

## Scalability

The core of this design is to abstract data synchronization into two processes: export (read) and import (write), completely decoupled, so it has good scalability. Each data source only needs to implement the two operations of read and write. Taking common data sources as an example, let's see how to import data from CSV (exporting to CSV is easy, can be implemented using any programming language).

| Data source | Import CSV |
| ------------- | ------------------------------------------------------------ |
| MySQL | Use `LOAD DATA LOCAL INFILE` for batch loading, or read the file to run the `INSERT` statement |
| AWS Redshift | Use AWS S3 as a transfer, and use the `COPY` command for batch loading |
| Hive | Specify the Serde as `org.apache.hadoop.hive.serde2.OpenCSVSerde` when creating the table, or convert the CSV to the default `TEXTFILE` format before importing; then use `LOAD DATA [LOCAL] INPATH` for batch loading. |
| ElasticSearch | Read the file and insert in batches |
| FTP, AWS S3 | Upload directly |

## Performance Issues

Another benefit of decoupling is performance optimization, because we can focus on optimizing export and import without worrying about the impact of each other.

### Export Performance

Export performance optimization is usually achieved through parallelization, that is, the data set is split and then processed in parallel.

Taking MySQL as an example, if the table has an auto-increment primary key, first query the upper and lower bounds, split into N pieces, and then start M threads to consume (Sqoop also uses this approach, by adjusting the number of mappers to control). Each thread can write a separate file and then merge, or use a separate thread to aggregate and write; generally speaking, the first method is better in terms of performance.

The premise of this optimization is to find a way to split as evenly as possible. If there is data skew, the improvement may not be significant, or even degrade to single thread. For the database, the field used for splitting also needs to have an index, and generally a auto-increment primary key or a timestamp with an index will be selected. The parallelism cannot be too high, otherwise it may bring too much pressure to the upstream system. Another implementation detail is that the data should be streamed to get and write to the file, rather than pulling all into memory, otherwise it may cause too much memory usage, or even OOM.

In addition, considering that the export process may be interrupted abnormally, you can also consider using a checkpoint mechanism to retry from the failure.

### Import Performance

Import performance optimization is usually achieved through the batch idea.

Some databases, such as MySQL, Hive, Redshift, etc., support directly loading CSV files, which is generally the most efficient way. If batch loading is not supported, you can also call the batch import API (such as ElasticSearch's `/_bulk`, the database's `INSERT` statement usually supports inserting multiple records at once). Some data sources may support compressed files (such as Redshift supports GZIP and other compression formats), you can compress before importing to shorten the transmission time and bandwidth consumption.

The failure retry of the import process can also use the checkpoint to achieve "resuming from the breakpoint", and you can also consider using a deduplication mechanism, such as using a bloom filter for checking.

## Complexity

From the design diagram in the previous section, you can see that this solution has low complexity, clear process, and easy to implement. Except for the local file system, there are basically no external dependencies. Pay attention to logs and statistics during implementation, which is convenient for tracking progress, analyzing problems, and locating faults.

## Full and Incremental

From the perspective of complexity, full synchronization is the easiest to implement and better guarantees the consistency of the data. However, as the data volume increases, the resource consumption and time required for each full synchronization will increase. Incremental synchronization is necessary and more complex.

### Incremental Export

The premise of incremental export is to be able to identify new data. The easiest way is to judge by the auto-increment primary key, but this is limited by the characteristics of the database itself. Some databases do not support auto-increment primary keys, and some databases do not guarantee monotonicity of auto-increment primary keys (such as [TiDB](<https://pingcap.com/docs/sql/mysql-compatibility/#auto-increment-id>), deploying multiple tidb-servers may result in the ID inserted later being smaller than the ID inserted earlier). It is more reliable to judge by time, time naturally increases and is strictly monotonic, and another benefit is that for periodic incremental synchronization, you don't need to save the checkpoint, you can calculate it directly.

Having a monotonically increasing integer or time field (preferably time) is a necessary condition for incremental export, and in order to better export performance, this field also needs to be indexed.

### Incremental Import

Incremental import needs to consider more situations, such as import mode and idempotence.

First, let's look at the import mode, which can be divided into two types: merge (`MERGE`) and append (`APPEND`) (in fact, there is also a special incremental import, such as importing to a partition of Hive, which is the same as full import (`OVERWRITE`)).

- `MERGE`: The new and updated records in the upstream system need to be synchronized to the target system, similar to `UPSERT`

- `APPEND`: The upstream system only adds, does not update, similar to `INSERT`

The implementation of `APPEND` is relatively simple, but if imported multiple times, (when there is no unique constraint) it is easy to generate duplicate data (not idempotent). In fact, `APPEND` is an extreme case of `MERGE`, so it can be converted to `MERGE` for implementation.

The premise of implementing `MERGE` is that you need a field to distinguish the uniqueness of the record, such as a primary key, a unique constraint (as long as it can be logically distinguished). Different data sources implement `MERGE` in different ways. Some data sources support `UPSERT` operation, such as Phoenix, Kudu, MongoDB, etc.; ElasticSearch is also similar to `UPSERT` when indexing documents; some databases support `REPLACE` operation; MySQL also has `INSERT ON DUPLICATE UPDATE`. In fact, for MySQL, Redshift, Hive and other relational databases, there is also a general solution: use `FULL JOIN` or `LEFT JOIN + UNION ALL` (refer to [Talking about Idempotence](http://liyangliang.me/posts/2019/03/idempotence/)).

This implementation of incremental import has a limitation, that is, it cannot synchronize the physical delete operation of the upstream system. If there is such a requirement, you can consider changing to soft delete, or using full synchronization.

### Import Process

Whether it is full or incremental, the import process needs to ensure at least two points: "transactionality" and cannot (as little as possible) affect the use of the target data. This problem mainly occurs in the database system, and generally does not occur in scenarios such as ElasticSearch and object storage.

"Transactionality" means that for the data to be imported, either all succeed or all fail, and partial import cannot occur.

During the import process, the target data should be available, or the affected time should be as short as possible. For example, long-term table locking should not occur, causing queries to fail.

You can optimize the process: first import to the staging table, prepare the final result table, and then replace it with the target table. When importing to the staging table, you can keep deleting and retrying, to ensure that the new data is completely imported before proceeding to the next step. For full import, you can directly rename the staging table to the target table, or use the `INSERT OVERWRITE` statement to copy the data. For incremental import, you need to create an intermediate table to store the result data, and after completing, use the rename or data copy method to update to the target table.

## Limitations

There are mainly two limitations: 1. Need to write to disk; 2. CSV.

In some scenarios, writing to disk may bring some additional performance overhead, but in the offline system, this impact should be negligible. Pay attention to file cleaning, otherwise the entire disk space may be used up. The biggest problem should be that the export and import are not completely decoupled, and must be deployed on the same machine, and ensure that the same file path is used. Because of this state, it to some extent limits the ability to horizontally scale (note, only the synchronization of a single table needs to be completed on one machine, and multiple tables can be horizontally scaled).

Using CSV files as a data exchange format is actually a compromise, with both advantages and disadvantages. Regarding the CSV format, there is also a discussion in [this article](http://liyangliang.me/posts/2019/03/data-encoding/). Here is a summary of the shortcomings:

- Cannot distinguish between numbers and strings that happen to be composed of numbers. However, this can be solved by using an additional schema, such as exporting the data at the same time, also exporting a schema, or using the schema of the target database to determine when importing.
- Does not support binary data.
- There may be escape problems.
- Cannot distinguish between empty strings and null values (`None`, `NULL`), one solution is to use a special value to represent null values, such as `\N`.

Overall, using CSV should be able to meet more than 90% of the use cases.

Using Kafka as a data exchange bus can break these limitations, but it also increases the complexity of the system. You can choose according to the actual situation.
