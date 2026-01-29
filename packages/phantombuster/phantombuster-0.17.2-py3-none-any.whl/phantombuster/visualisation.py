from bokeh.models import Plot
from bokeh.io import export_svg
import numpy as np


def _make_backend_svg(p):
    if isinstance(p, Plot):
        p.output_backend = "svg"
    else:
        if hasattr(p, "children"):
            for child in p.children:
                _make_backend_svg(child)
        else:
            try:
                for child in p:
                    _make_backend_svg(child)
            except:
                pass


def save(p, output=None):
    """Save a bokeh plot as svg"""
    _make_backend_svg(p)
    if not output.endswith(".svg"):
        output += ".svg"
    export_svg(p, filename=output)


def pixel_filter(x, y, nx, ny, glyph_size, frame_width, frame_height, x_range, y_range, pixel_overlap):

    x_pixel = frame_width * (nx - x_range[0]) / (x_range[1] - x_range[0])
    y_pixel = frame_height * (ny - y_range[0]) / (y_range[1] - y_range[0])

    mask = np.ones(len(x_pixel), dtype=bool)

    xo, yo = np.inf, np.inf

    for idx, (xx, yy) in enumerate(zip(x_pixel, y_pixel)):
        dist = np.sqrt((xx-xo)**2 + (yy-yo)**2)
        if dist > pixel_overlap * glyph_size:
            xo, yo = xx, yy
        else:
            mask[idx] = False
    mask[0] = True
    mask[-1] = True
    return x[mask], y[mask]


def make_ranked(data, frame_width=200, frame_height=200, filter_pixels=False, **kwargs):
    r = np.sort(data)[::-1]
    ranks = np.arange(len(r))+1
    if filter_pixels:
        ranks, r = pixel_filter(ranks, r, np.log10(ranks), np.log10(r), 1, frame_width, frame_height, (0, np.log10(len(r))), (np.log10(np.min(r)), np.log10(np.max(r))), 1)
    source = ColumnDataSource({'Rank': ranks, 'Reads': r})
    p = figure(x_axis_type="log", y_axis_type="log", x_axis_label="Rank", y_axis_label="Reads", frame_width=frame_width, frame_height=frame_height, **kwargs)

    view = CDSView(filter=make_pixel_filter(p, source, 'Rank', 'Reads', 1.0, 1.0))
    p.circle('Rank', 'Reads', source=source, view=view)
    return p


def make_threshold(p, max_rank, name, thresholds):
    TH = thresholds.get(name, 5)
    source_tmp = ColumnDataSource({"threshold": [TH, TH], "ranks": [1/2, max_rank*2]})
    tmp_renderer = p.line(x="ranks", y="threshold", color="red", alpha=0.5, source=source_tmp)

    source_persistent = ColumnDataSource({"name": [name, name], "threshold": [TH, TH], "ranks": [1/2, max_rank*2]})
    persistent_renderer = p.line(x="ranks", y="threshold", color="red", source=source_persistent)

    update_threshold = CustomJS(args={'source': source_tmp, 'p':p}, code="""
    source.data["threshold"][0] = cb_obj['y'];
    source.data["threshold"][1] = cb_obj['y'];
    source.change.emit();
    """)

    p.js_on_event(bokeh.events.MouseMove, update_threshold)

    hide_tmp = CustomJS(args={'renderer': tmp_renderer}, code='renderer.visible = false;')
    show_tmp = CustomJS(args={'renderer': tmp_renderer}, code='renderer.visible = true;')

    p.js_on_event(bokeh.events.MouseEnter, show_tmp)
    p.js_on_event(bokeh.events.MouseLeave, hide_tmp)

    set_threshold = CustomJS(args={'source': source_persistent, 'p':p}, code="""
    source.data["threshold"][0] = Math.round(cb_obj['y']);
    source.data["threshold"][1] = Math.round(cb_obj['y']);
    source.change.emit();
    """)

    p.js_on_event(bokeh.events.Tap, set_threshold)
    p.js_on_event(bokeh.events.DoubleTap, set_threshold)
    return source_persistent


def make_download(download_sources):
    DOWNLOAD_CODE = """
    function sources_to_csv(sources) {
        const lines = ['sample,threshold']
        for (let i = 0; i<sources.length; i++) {
            var s = sources[i].data;
            lines.push(s['name'][0] + ',' + s['threshold'][0]);
        }
        return lines.join('\\n').concat('\\n');
    }
    console.log(sources);

    const filename = download_name;
    const filetext = sources_to_csv(sources);
    const blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.target = '_blank'
    link.style.visibility = 'hidden'
    link.dispatchEvent(new MouseEvent('click'))
    """

    button = Button(label="Download", button_type="success")
    button.js_on_click(CustomJS(args={'sources':download_sources, 'download_name': 'thresholds.csv'} ,code=DOWNLOAD_CODE))
    return button

def generate_data(df, col):
    stats = df.group_by(col).agg([pl.count().alias("count"), pl.col("reads").max()]).select([pl.col("count").max(), pl.col("reads").max()])
    max_rank = stats["count"][0]
    max_reads = stats["reads"][0]

    sorted_data = df.group_by(col).agg(pl.col("reads")).sort(pl.col(col))
    return max_rank, max_reads, sorted_data


#df = pl.read_csv("data/thresholds.csv")
#THRESHOLDS = dict(zip([str(sample) for sample in df["sample"]], df["threshold"]))

def make_visualisation(df, col, thresholds)
    max_rank, max_reads, sorted_data = generate_data(df, col)



ps = []
download_sources = []
for sample, data in zip(sorted_data["sample"], sorted_data["reads"]):
    print(sample)
    data = np.sort(np.array(data))[::-1]
    p = make_ranked(data, title=sample, x_range=(1/2, max_rank*2), y_range=(1/2, max_reads*2), filter_pixels=True)
    download_source = make_threshold(p, max_rank, sample)
    download_sources.append(download_source)
    p.title.text_font_size = "14pt"
    p.xaxis.visible = False
    p.yaxis.visible = False
    ps.append(p)

download_button = make_download(download_sources)

for i, p in enumerate(ps):
    if i % 8 == 0:
        p.yaxis.visible = True
for p in ps[-8:]:
    p.xaxis.visible = True

show(column([download_button, grid(ps, ncols=8)]))

save(grid(ps, ncols=8), 'ranked_cscr.svg')


