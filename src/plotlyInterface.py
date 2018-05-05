import plotly.offline as py

class plotlyInterface:
    
    def __init__(self, data, layout = {}):
        self.fig = {'data': data, 'layout': layout}
        
    # ==============================================================================================================================
    def plotToFile(self, filename = 'test.html', **kwargs):
        kwargs['figure_or_data'] = self.fig
        kwargs['filename'] = filename
        kwargs['auto_open'] = False
        py.plot(**kwargs)
    
    # ==============================================================================================================================
    def plotToHtml(self, **kwargs):
        kwargs['figure_or_data'] = self.fig
        kwargs['output_type'] = 'div'
        kwargs['include_plotlyjs'] = False ## do that once upfront manually
        return py.plot(**kwargs)
        