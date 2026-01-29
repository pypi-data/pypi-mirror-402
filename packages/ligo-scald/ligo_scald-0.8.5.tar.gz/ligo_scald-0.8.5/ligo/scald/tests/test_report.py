from ligo.scald import report


class TestReport(object):
    """
    Tests several aspects of report.py to check basic functionality.
    """
    def test_content(self):
        plots = [
            report.Plot('plot'),
            report.ScatterPlot('plot'),
            report.Heatmap('plot'),
            report.BarGraph('plot'),
        ]
        for plot in plots:
            assert plot.title == 'plot', 'plot title expected: {}, got: {}'.format('plot', plot.title)
            for c in ['title', 'layout', 'options', 'data_options']:
                assert c in plot.content, 'missing content {} for {}'.format(c, plot)

        image = report.Image(url='test_url')
        assert image.url == 'test_url', 'plot title expected: {}, got: {}'.format('test_url', image.url)

        plot_grid = report.PlotGrid(title='test', grid_size=4)
        for plot in plots:
            plot_grid += plot
        assert plot_grid.content['title'] == 'test', 'plot grid title expected: {}, got: {}'.format('test', plot_grid.content['title'])
        assert plot_grid.grid_size == 4, 'plot grid size expected: {}, got: {}'.format(4, plot_grid.grid_size)
        assert len(plot_grid) == len(plots), 'number of plots in plot grid expected: {}, got: {}'.format(len(plots), len(plot_grid))

        image_grid = report.ImageGrid(title='test', grid_size=4)
        image_grid += image
        assert image_grid.grid_size == 4, 'image grid size expected: {}, got: {}'.format(4, image_grid.grid_size)
        assert image_grid.title == 'test', 'image grid title expected: {}, got: {}'.format('test', plot_grid.title)
        assert len(image_grid) == 1, 'number of images in image grid expected: {}, got: {}'.format(1, len(image_grid))


    def test_tabs(self):
        tab = report.Tab('test_tab')
        plots = [
            report.Plot('plot'),
            report.ScatterPlot('plot'),
            report.Heatmap('plot'),
            report.BarGraph('plot'),
        ]
        for i, plot in enumerate(plots, 1):
            tab += plot

        assert 'name' in tab.tab, 'missing name in tab'
        assert 'content' in tab.tab, 'missing content in tab'
        assert 'url' not in tab.tab, 'unexpected url in tab'
