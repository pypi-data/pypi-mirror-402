"""
This file is taken from SQLAlchemy
"""


class AbstractKeyedTuple(tuple):
    __slots__ = ()

    def keys(self):
        """Return a list of string key names for this :class:`.KeyedTuple`.

        .. seealso::

            :attr:`.KeyedTuple._fields`

        """

        return list(self._fields)


class KeyedTuple(AbstractKeyedTuple):
    """``tuple`` subclass that adds labeled names.

    E.g.::

        >>> k = KeyedTuple([1, 2, 3], labels=["one", "two", "three"])
        >>> k.one
        1
        >>> k.two
        2

    Result rows returned by :class:`.Query` that contain multiple
    ORM entities and/or column expressions make use of this
    class to return rows.

    The :class:`.KeyedTuple` exhibits similar behavior to the
    ``collections.namedtuple()`` construct provided in the Python
    standard library, however is architected very differently.
    Unlike ``collections.namedtuple()``, :class:`.KeyedTuple` is
    does not rely on creation of custom subtypes in order to represent
    a new series of keys, instead each :class:`.KeyedTuple` instance
    receives its list of keys in place.   The subtype approach
    of ``collections.namedtuple()`` introduces significant complexity
    and performance overhead, which is not necessary for the
    :class:`.Query` object's use case.

    .. seealso::

        :ref:`ormtutorial_querying`

    """

    def __new__(cls, vals, labels=None):
        t = tuple.__new__(cls, vals)
        if labels:
            t.__dict__.update(zip(labels, vals))
        else:
            labels = []
        t.__dict__["_labels"] = labels
        return t

    @property
    def _fields(self):
        """Return a tuple of string key names for this :class:`.KeyedTuple`.

        This method provides compatibility with ``collections.namedtuple()``.

        .. seealso::

            :meth:`.KeyedTuple.keys`

        """
        return tuple([l for l in self._labels if l is not None])

    def __setattr__(self, key, value):
        raise AttributeError("Can't set attribute: %s" % key)

    def _asdict(self):
        """Return the contents of this :class:`.KeyedTuple` as a dictionary.

        This method provides compatibility with ``collections.namedtuple()``,
        with the exception that the dictionary returned is **not** ordered.

        """
        return {key: self.__dict__[key] for key in self.keys()}
