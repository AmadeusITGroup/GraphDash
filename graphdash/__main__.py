#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import app, CONF


def main():
    app.run('0.0.0.0', port=CONF['port'], debug=CONF['debug'])


if __name__ == '__main__':
    main()
