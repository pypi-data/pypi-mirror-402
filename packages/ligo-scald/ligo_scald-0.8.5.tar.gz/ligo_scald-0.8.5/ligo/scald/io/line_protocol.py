# -*- coding: utf-8 -*-
"""Define the line_protocol handler."""

#  The MIT License (MIT)
#  
#  Copyright (c) 2013 InfluxDB
#  
#  Permission is hereby granted, free of charge, to any person obtaining a copy of
#  this software and associated documentation files (the "Software"), to deal in
#  the Software without restriction, including without limitation the rights to
#  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#  the Software, and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#  
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


def _escape_tag(tag):
    tag = _get_unicode(tag, force=True)
    return tag.replace(
        "\\", "\\\\"
    ).replace(
        " ", "\\ "
    ).replace(
        ",", "\\,"
    ).replace(
        "=", "\\="
    )


def _escape_tag_value(value):
    ret = _escape_tag(value)
    if ret.endswith('\\'):
        ret += ' '
    return ret


def quote_indent(value):
    """Indent the quotes."""
    return "\"{}\"".format(value
                           .replace("\\", "\\\\")
                           .replace("\"", "\\\"")
                           .replace("\n", "\\n"))


def quote_literal(value):
    """Quote provided literal."""
    return "'{}'".format(value
                         .replace("\\", "\\\\")
                         .replace("'", "\\'"))


def _is_float(value):
    try:
        float(value)
    except (TypeError, ValueError):
        return False

    return True


def _escape_value(value):
    value = _get_unicode(value)

    if isinstance(value, str) and value != '':
        return quote_indent(value)
    elif isinstance(value, int) and not isinstance(value, bool):
        return str(value) + 'i'
    elif _is_float(value):
        # Convert to Python float to ensure correct repr() output.
        # NumPy 2.0+ changed repr(np.float64(x)) from "x" to "np.float64(x)"
        return repr(float(value))

    return str(value)


def _get_unicode(data, force=False):
    """Try to return a text aka unicode object from the given data."""
    if isinstance(data, bytes):
        return data.decode('utf-8')
    elif data is None:
        return ''
    elif force:
        return str(data)
    else:
        return data


def make_lines(data):
    """Extract points from given dict.

    Extracts the points from the given dict and returns a Unicode string
    matching the line protocol introduced in InfluxDB 0.9.0.
    """
    lines = []
    static_tags = data.get('tags')
    for point in data['points']:
        elements = []

        # add measurement name
        measurement = _escape_tag(_get_unicode(
            point.get('measurement', data.get('measurement'))))
        key_values = [measurement]

        # add tags
        if static_tags:
            tags = dict(static_tags)  # make a copy, since we'll modify
            tags.update(point.get('tags') or {})
        else:
            tags = point.get('tags') or {}

        # tags should be sorted client-side to take load off server
        for tag_key, tag_value in sorted(tags.items()):
            key = _escape_tag(tag_key)
            value = _escape_tag_value(tag_value)

            if key != '' and value != '':
                key_values.append(key + "=" + value)

        elements.append(','.join(key_values))

        # add fields
        field_values = []
        for field_key, field_value in sorted(point['fields'].items()):
            key = _escape_tag(field_key)
            value = _escape_value(field_value)

            if key != '' and value != '':
                field_values.append(key + "=" + value)

        elements.append(','.join(field_values))

        # add timestamp
        if 'time' in point:
            timestamp = _get_unicode(str(point['time']))
            elements.append(timestamp)

        line = ' '.join(elements)
        lines.append(line)

    return '\n'.join(lines) + '\n'
