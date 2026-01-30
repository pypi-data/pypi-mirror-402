import os
import threading

_default_error_rate = 1 / 10**8  # 亿分之一


class _BloomFilterInterface(object):
    def __init__(self, filename, capacity=100, error_rate=_default_error_rate, auto_scale=True, reuse=True):
        self.filename = filename

    def __len__(self):
        raise NotImplementedError

    def __contains__(self, item):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError

    def add(self, key):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def close(self):
        pass


class PyBloomFilter(_BloomFilterInterface):
    def __init__(self, filename, capacity=100, error_rate=_default_error_rate, auto_scale=True, reuse=True):
        import pybloom_live

        super().__init__(filename, capacity, error_rate, auto_scale, reuse)

        if auto_scale:
            filter_cls = pybloom_live.ScalableBloomFilter
        else:
            filter_cls = pybloom_live.BloomFilter

        if reuse and os.path.exists(filename):
            with open(filename, "rb") as f:
                self._bf = filter_cls.fromfile(f)
        else:
            self._bf = filter_cls(capacity, error_rate)

        self._lock = threading.RLock()

    def __getattr__(self, name):
        with self._lock:
            return getattr(self._bf, name)

    def __len__(self):
        with self._lock:
            return len(self._bf)

    def __str__(self):
        return f"<{self.__class__.__name__} ({repr(self.filename)}, capacity={self.capacity}, count={self.count})>"

    def __contains__(self, item):
        with self._lock:
            return item in self._bf

    def add(self, key):
        with self._lock:
            return self._bf.add(key)

    def save(self):
        with self._lock:
            with open(self.filename, "wb") as f:
                self._bf.tofile(f)

    def close(self):
        self.save()


class CBloomFilter(_BloomFilterInterface):
    def __init__(self, filename, capacity, error_rate=_default_error_rate, auto_scale=True, reuse=True):
        import pybloomfilter

        super().__init__(filename, capacity, error_rate, auto_scale, reuse)

        # pybloomfilter 不支持自动 scale，必须给定 capacity
        if reuse and os.path.exists(filename):
            self._bf = pybloomfilter.BloomFilter.open(filename)
        else:
            self._bf = pybloomfilter.BloomFilter(capacity, error_rate, filename)
        self._lock = threading.RLock()

    @property
    def count(self):
        return len(self)

    @property
    def capacity(self):
        return self._bf.capacity

    def __contains__(self, item):
        with self._lock:
            return item in self._bf

    def __len__(self):
        with self._lock:
            return len(self._bf)

    def __str__(self):
        return f"<{self.__class__.__name__} ({repr(self.filename)}, capacity={self.capacity}, count={self.count})>"

    def add(self, key):
        with self._lock:
            return self._bf.add(key)

    def save(self):
        with self._lock:
            self._bf.sync()

    def close(self):
        self._bf.close()


class DummyBloomFilter(_BloomFilterInterface):
    def __len__(self):
        return 0

    def __contains__(self, item):
        return False

    def __str__(self):
        return self.__class__.__name__

    def add(self, key):
        return False

    def save(self):
        pass


_engine_choices = {
    "C": CBloomFilter,
    "py": PyBloomFilter,
    "dummy": DummyBloomFilter,
    "None": DummyBloomFilter,
}


def new_bloom_filter(filename, capacity, error_rate=_default_error_rate, auto_scale=True, reuse=True, engine="py"):
    if engine is None:
        engine = "None"
    engine = engine or "py"
    return _engine_choices[engine](filename, capacity, error_rate, auto_scale, reuse)


def __benchmark(filename, capacity, error_rate, engine):
    import datetime

    values = range(capacity)
    f = new_bloom_filter(filename, capacity, error_rate, reuse=False, engine=engine)
    st = datetime.datetime.now()
    for i in values:
        if i not in f:
            f.add(i)
    f.save()
    duration = datetime.datetime.now() - st
    qps = len(values) / duration.total_seconds()
    print(engine, f, duration, qps)


if __name__ == "__main__":
    # C <CBloomFilter ('/tmp/bloom_C', capacity=2000000, count=1999740)> 0:00:03.047118 656357.9093425327
    # C <CBloomFilter ('/tmp/bloom_C', capacity=2000000, count=1999766)> 0:00:02.591953 771618.9298185576
    # C <CBloomFilter ('/tmp/bloom_C', capacity=2000000, count=1999737)> 0:00:02.756158 725647.8039357685
    # py <PyBloomFilter ('/tmp/bloom_py', capacity=2000000, count=1999770)> 0:00:33.104276 60415.15603603595
    # py <PyBloomFilter ('/tmp/bloom_py', capacity=2000000, count=1999770)> 0:00:33.406134 59869.244372904686
    # py <PyBloomFilter ('/tmp/bloom_py', capacity=2000000, count=1999770)> 0:00:34.070549 58701.725058789045
    # None DummyBloomFilter 0:00:00.431990 4629736.799462951
    # None DummyBloomFilter 0:00:00.432359 4625785.51620297
    # None DummyBloomFilter 0:00:00.432572 4623507.762869534
    for x in ["C", "py", "None"]:
        fn = f"/tmp/bloom_{x}"
        for _ in range(3):
            __benchmark(fn, capacity=10000000, error_rate=0.001, engine=x)
