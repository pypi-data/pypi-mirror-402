import glob
import json
import os
import shutil
import sys

from . import resources

import bottle
import yaml

from .io import core


template_path = resources.get_resource_path('templates')
bottle.TEMPLATE_PATH.insert(0, template_path)


class Report(object):
    def __init__(self, title='', image=None, tabs=None, theme=None, **kwargs):
        self.title = title
        self.image = image
        self.theme = theme
        if tabs:
            self.tabs = tabs
        else:
            self.tabs = []

        self.report = {'report': {'title': self.title, 'tabs': self.tabs}}
        if self.image:
            self.report['report'].update({'image': self.image})
        if self.theme:
            self.report['report'].update({'theme': self.theme})
        if 'detector' in kwargs:
            self.report['report'].update({'detector': kwargs['detector']})

    def __str__(self):
        return str(self.report)

    def __iadd__(self, tab):
        if isinstance(tab, list):
            self.report['report']['tabs'].extend([t.tab for t in tab])
        else:
            self.report['report']['tabs'].append(tab.tab)
        return self

    def save_config(self, savedir, config_name='report'):
        """
        Creates a configuration file containing all the content
        needed to produce an offline-style report with scald report.
        """
        with open(os.path.join(savedir, '.'.join([config_name, 'yml'])), 'w') as f:
            yaml.dump(self.report, f, default_flow_style=False)

    def save(self, savedir, config_name='report'):
        """
        Generates a report as well as a config file that was used to generate
        this report.
        """
        ### save config
        self.save_config(savedir, config_name=config_name)

        ### copy over static files
        static_dir = resources.get_resource_path('static')
        try:
            if sys.version_info >= (3, 8):
                shutil.copytree(static_dir, os.path.join(savedir, 'static'), dirs_exist_ok=True)
            else:
                # fallback for Python < 3.8
                from distutils import dir_util
                dir_util.copy_tree(static_dir, os.path.join(savedir, 'static'))
        except OSError:
            pass

        ### save content and generate urls
        core.makedir(os.path.join(savedir, 'data'))
        core.makedir(os.path.join(savedir, 'images'))
        for i, tab_config in enumerate(self.report['report']['tabs']):
            if 'content' in tab_config.keys():
                tab_config['url'] = '{}.html'.format(tab_config['name'].lower().replace(' ', '_')) if i != 0 else 'index.html'
                save_content(savedir, tab_config['content'])

        ### generate report
        for tab_config in self.report['report']['tabs']:
            if 'content' in tab_config.keys():
                report = bottle.template('report.html', content=tab_config['content'], config=self.report['report'])
                with open(os.path.join(savedir, tab_config['url']), 'w') as f:
                    f.write(report)


class Tab(object):
    def __init__(self, name, url=None):
        self.url = url
        self.name = name
        self.content = []

        if self.url:
            self.tab = {'name': self.name, 'url': self.url}
        else:
            self.tab = {'name': self.name, 'content': self.content}

    def __str__(self):
        return str(self.tab)

    def __iadd__(self, content):
        if not self.url:
            if isinstance(content, list):
                self.tab['content'].extend([c.content for c in content])
            else:
                self.tab['content'].append(content.content)
            return self
        else:
            raise ValueError('content not allowed to be added in if url is set')


class Content(object):
    _type = 'base'

    def __init__(self, *args, **kwargs):
        self.content = {'name': self._type}

    def __str__(self):
        return str(self.content)


class Plot(Content):
    _type = 'plot'
    _def_layout = {}
    _def_data_options = {}
    _def_options = {}

    def __init__(self, title, path=None, url=None, data_options = None, layout = None, options = None, **kwargs):
        super(Plot, self).__init__(title, **kwargs)
        self.title = title
        self._layout = self._def_layout
        self._data_options = self._def_data_options
        self._options = self._def_options

        if data_options:
            self._data_options.update(data_options)
        self.content.update({'data_options': self._data_options})
        if layout:
            self._layout.update(layout)
        self.content.update({'layout': self._layout})
        if options:
            self._options.update(options)
        self.content.update({'options': self._options})
        self.content.update({'title': self.title})
        self.content.update(kwargs)

    def save(self, data, savedir, **kwargs):
        datapath = os.path.join(savedir, '{}_data.json'.format(self.title))
        with open(datapath, 'w') as f:
            f.write(json.dumps([data]))

        self.content['path'] = datapath


class ScatterPlot(Plot):
    _def_data_options = {'mode': 'markers'}
    _def_layout = {
        'font': {
            'family': 'Noto Serif TC',
            'size': 11
        },
        'xaxis': {
            'tickformat': 'd',
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        },
        'yaxis': {
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        }
    }
    _def_options = {'displayModeBar': False}


class Heatmap(Plot):
    _def_data_options = {'type': 'heatmap', 'mode':'markers'}
    _def_layout = {
        'font': {
            'family': 'Noto Serif TC',
            'size': 11
        },
        'xaxis': {
            'tickformat': 'd',
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        },
        'yaxis': {
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        }
    }
    _def_options = {'displayModeBar': False}


class LinePlot(Plot):
    _def_data_options = {}
    _def_layout = {
        'font': {
            'family': 'Noto Serif TC',
            'size': 11
        },
        'xaxis': {
            'tickformat': 'd',
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        },
        'yaxis': {
            'linecolor': 'black',
            'mirror': 'allticks',
            'ticks': 'inside'
        }
    }
    _def_options = {'displayModeBar': False}


class BarGraph(Plot):
    _def_data_options = {'type' : 'bar'}
    _def_layout = {'font': {'family': 'Noto Serif TC', 'size': 11}}
    _def_options = {'displayModeBar': False}


class PlotGrid(Content):
    _type = 'plot_grid'

    def __init__(self, grid_size=6, **kwargs):
        super(PlotGrid, self).__init__(**kwargs)
        self.grid_size = grid_size
        self.plots = []

        self.content = {'title': '', 'plots': self.plots, 'grid_size': self.grid_size}
        self.content.update(kwargs)

    def __iadd__(self, plot):
        self.plots.append(plot.content)
        return self

    def __len__(self):
        return len(self.plots)


class Image(Content):
    _type = 'image'

    def __init__(self, path=None, url=None, **kwargs):
        super(Image, self).__init__(**kwargs)
        self.path = path
        self.url = url

        if path:
            self.content.update({'path': self.path})
        else:
            self.content.update({'url': self.url})
        self.content.update(kwargs)


class ImageGrid(Content):
    _type = 'image_grid'

    def __init__(self, title, grid_size=6, footer=None, visible=True, **kwargs):
        super(ImageGrid, self).__init__(**kwargs)
        self.title = title
        self.grid_size = grid_size
        self.visible = visible
        self.footer = footer
        self.images = []

        self.content.update({'title': self.title, 'images': self.images, 'grid_size': self.grid_size, 'visible': self.visible})
        if self.footer:
            self.content['footer'] = self.footer
        self.content.update(kwargs)

    def __iadd__(self, image):
        self.images.append(image.content)
        return self

    def __len__(self):
        return len(self.images)

    def glob(self, glob_path):
        for path in sorted(glob.glob(glob_path)):
            self.images.append(Image(path=path).content)
        return self


class ImageBoard(Content):
    _type = 'image_board'

    def __init__(self, title, images=None, **kwargs):
        super(ImageBoard, self).__init__(**kwargs)
        self.title = title
        if images:
            self.images = [[Image(path).content for path in image_row] for image_row in images]
        else:
            self.images = []

        self.content.update({'title': self.title, 'images': self.images})
        self.content.update(kwargs)

    def __len__(self):
        return len(self.images)


class ImagePagination(Content):
    _type = 'image_pagination'

    def __init__(self, title, footer=None, visible=True, **kwargs):
        super(ImagePagination, self).__init__(**kwargs)
        self.title = title
        self.visible = visible
        self.footer = footer
        self.images = []

        self.content.update({'title': self.title, 'images': self.images, 'visible': self.visible})
        if self.footer:
            self.content['footer'] = self.footer
        self.content.update(kwargs)

    def __iadd__(self, image):
        self.images.append(image.content)
        return self

    def __len__(self):
        return len(self.images)

    def glob(self, glob_path):
        for path in sorted(glob.glob(glob_path)):
            self.images.append(Image(path=path).content)
        self.images.sort(key = lambda x: x['path'])
        return self


class FlatTable(Content):
    _type = 'flat_table'

    def __init__(self, title, columns=None, rows=None, **kwargs):
        super(FlatTable, self).__init__(title, **kwargs)
        self.title = title
        self.columns = columns
        self.rows = None

        self.content.update({'title': self.title, 'columns': columns, 'rows': rows})
        self.content.update(kwargs)


class Table(Content):
    _type = 'table'

    def __init__(self, title, footer=None, visible=True, **kwargs):
        super(Table, self).__init__(title, **kwargs)
        self.title = title
        self.visible = visible
        self.footer = footer

        self.content.update({'title': self.title, 'visible': self.visible})
        if self.footer:
            self.content['footer'] = self.footer
        self.content.update(kwargs)

    def save(self, data, savedir, **kwargs):
        filename = '{}_table.json'.format(self.title).lower().replace(' ', '_')
        datapath = os.path.join(savedir, 'data', filename)
        core.makedir(os.path.join(savedir, 'data'))

        ### write formatted data to disk
        with open(datapath, 'w') as f:
            f.write(json.dumps(data))

        self.content['url'] = os.path.join('data', filename)
        return self


class Header(Content):
    _type = 'header'

    def __init__(self, header, **kwargs):
        super(Header, self).__init__(header, **kwargs)
        self.header = header
        self.content['header'] = self.header


class Footer(Content):
    _type = 'footer'

    def __init__(self, footer, **kwargs):
        super(Footer, self).__init__(footer, **kwargs)
        self.footer = footer
        self.content['footer'] = self.footer


class Description(Content):
    _type = 'description'

    def __init__(self, description, **kwargs):
        super(Description, self).__init__(description, **kwargs)
        self.description = description
        self.content['description'] = self.description


def save_content(webdir, config):
    for content in config:
        if 'image_grid' in content['name'] or 'image_pagination' in content['name']:
            for image in content['images']:
                if 'path' in image.keys():
                    shutil.copy2(image['path'], os.path.join(webdir, 'images'))
                    image['url'] = os.path.join('images', os.path.basename(image['path']))
        elif 'image_board' in content['name']:
            for image_row in content['images']:
                for image in image_row:
                    if 'path' in image.keys():
                        shutil.copy2(image['path'], os.path.join(webdir, 'images'))
                        image['url'] = os.path.join('images', os.path.basename(image['path']))
        elif 'plot_grid' in content['name']:
            for plot in content['plots']:
                if 'path' in plot.keys():
                    shutil.copy2(plot['path'], os.path.join(webdir, 'data'))
                    plot['url'] = os.path.join('data', os.path.basename(plot['url']))
        elif 'image' in content['name'] and 'path' in content:
            shutil.copy2(content['path'], os.path.join(webdir, 'images'))
            content['url'] = os.path.join('images', os.path.basename(content['path']))
        elif 'plot' in content['name'] and 'path' in content:
            shutil.copy2(content['path'], os.path.join(webdir, 'data'))
            content['url'] = os.path.join('data', os.path.basename(content['path']))
        elif 'table' in content['name'] and 'path' in content:
            shutil.copy2(content['path'], os.path.join(webdir, 'data'))
            content['url'] = os.path.join('data', os.path.basename(content['path']))


def _add_parser_args(parser):
    parser.add_argument('-c', '--config', required=True,
                        help="sets specific plot and dashboard options based on yaml configuration.")
    parser.add_argument('-o', '--output-dir', default='.',
                        help="sets the directory where reports and related files are saved to.")


def main(args=None):
    """Generates offline html reports

    """
    if not args:
        parser = argparse.ArgumentParser()
        _parser_add_arguments(parser)
        args = parser.parse_args()

    ### parse args
    output_dir = args.output_dir

    ### load config file
    config = None
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    ### generate report
    report = Report(**config['report'])
    report.save(output_dir)
