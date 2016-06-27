# -*- coding: utf-8 -*-

"""
Tree implementation.
"""


class Tree(object):
    __slots__ = ['sons', 'parent', 'data', '__factory']

    def __init__(self, factory=dict):
        self.data = factory()
        self.__factory = factory
        self.sons = {}
        self.parent = None

    def create_from_path(self, path):
        if not path:
            return self
        first, others = path[0], path[1:]
        if first not in self.sons:
            self.sons[first] = Tree(factory=self.__factory)
            self.sons[first].parent = self

        return self.sons[first].create_from_path(others)

    def get_from_path(self, path):
        if not path:
            return self

        first, others = path[0], path[1:]
        if first not in self.sons:
            return

        return self.sons[first].get_from_path(others)

    @staticmethod
    def iter_upper_paths(path, include_root=True):
        if include_root:
            yield ()
        for i, _ in enumerate(path, start=1):
            yield path[:i]

    def iter_all_parents(self):
        if self.parent is not None:
            yield self.parent
            for parent in self.parent.iter_all_parents():
                yield parent

    def iter_all_nodes(self, path=()):
        yield path, self
        for son_name in self.sons:
            son = self.sons[son_name]
            for node_path, node in son.iter_all_nodes(path + (son_name,)):
                yield node_path, node

    def __prettify(self, decorate, with_data, sort_sons, index, name, indent):
        """Recursive pretty printer.
        """
        res = [u'{0}({1}) {2}'.format(indent, index, decorate((name, self)))]
        increment = '  '
        indent += increment

        if with_data is not None:
            for i, thing in enumerate(with_data(self.data), start=1):
                res.append(u'{0}|{1:2d}| {2}'.format(indent + increment, i, thing))

        for i, (son_name, son) in enumerate(sort_sons(self.sons.items()), start=1):
            res.append(son.__prettify(decorate, with_data, sort_sons, i, son_name, indent))

        return '\n'.join(res)

    def prettify(self, decorate=lambda x: '', with_data=None, sort_sons=lambda x: x):
        return self.__prettify(decorate=decorate,
                               with_data=with_data,
                               sort_sons=sort_sons,
                               index=1,
                               name='',
                               indent='')
