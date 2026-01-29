from bokeh.models import Plot, ColumnDataSource, CDSView
import bokeh.events
from bokeh.models import Legend, FactorRange, LabelSet, ColumnDataSource, CDSView, CustomJSFilter, CustomJS, Button
from bokeh.layouts import column, grid
from bokeh.plotting import figure
from bokeh.io import export_svg, save as save_html
import numpy as np
import polars as pl


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


def make_pixel_filter(p, source, x_column, y_column, pixel_overlap, glyph_size):
    custom_filter = CustomJSFilter(args={'p':p, 'x_column': x_column, 'y_column':y_column, 'pixel_overlap': pixel_overlap, 'glyph_size': glyph_size}, code='''
    const frame_width = p.frame_width;
    const frame_height = p.frame_height;
    var xo = Math.inf;
    var yo = Math.inf;

    const overlap = pixel_overlap * glyph_size;
    var total_pixels = 0;

    const x_low = Math.log(p.x_range.start);
    const x_high = Math.log(p.x_range.end);
    const y_low = Math.log(p.y_range.start);
    const y_high = Math.log(p.y_range.end);

    const x_col = source.data[x_column];
    const y_col = source.data[y_column];
    const l = source.get_length();

    if ((this._cached_frame_width === frame_width) &&
        (this._cached_frame_height === frame_height) &&
        (this._cached_x_range_start === p.x_range.start) &&
        (this._cached_x_range_end === p.x_range.end) &&
        (this._cached_y_range_start === p.y_range.start) &&
        (this._cached_y_range_end === p.y_range.end) &&
        (this._cached_pixel_overlap === pixel_overlap) &&
        (this._cached_glyph_size === glyph_size)) {
        console.log("cache hit");
        return this._cached_indices;
    }

    const indices = new Array(l);

    this._cached_frame_width = frame_width;
    this._cached_frame_height = frame_height;
    this._cached_x_range_start = p.x_range.start;
    this._cached_x_range_end = p.x_range.end;
    this._cached_y_range_start = p.y_range.start;
    this._cached_y_range_end = p.y_range.end;
    this._cached_pixel_overlap = pixel_overlap;
    this._cached_glyph_size = glyph_size;
    this._cached_indices = indices;




    for (let i = 0; i < l; i++){
        var x = frame_width * (Math.log(x_col[i]) - x_low) / (x_high - x_low);
        var y = frame_height * (Math.log(y_col[i]) - y_low) / (y_high - y_low);

        if ((x < 0 ) || (x>frame_width) || (y < 0) || ( y>frame_height) ){
            indices[i] = false;
        } else {

            var dist = Math.sqrt(Math.pow(x - xo, 2) + Math.pow(y - yo, 2))

            if ((dist > overlap) || (isNaN(dist))){
                xo = x;
                yo = y;
                indices[i] = true;
                total_pixels += 1;
            } else {
                indices[i] = false;
            }
        }
    }
    console.log(total_pixels);
    return indices;
    ''')

    refresh = CustomJS(args={'filter':custom_filter, 'source':source, "p": p, "pixel_overlap": pixel_overlap, "glyph_size": glyph_size}, code="""
    setTimeout(function() {
        if (filter._may_not_draw) {
            console.log("filter may not draw");
            return;
        }

        if ((filter._cached_frame_width === p.frame_width) &&
            (filter._cached_frame_height === p.frame_height) &&
            (filter._cached_x_range_start === p.x_range.start) &&
            (filter._cached_x_range_end === p.x_range.end) &&
            (filter._cached_y_range_start === p.y_range.start) &&
            (filter._cached_y_range_end === p.y_range.end) &&
            (filter._cached_pixel_overlap === pixel_overlap) &&
            (filter._cached_glyph_size === glyph_size)) {
            console.log("refresh cache hit");
        } else {
            source.change.emit();
        }
    });""")


    p.x_range.js_on_change('start', refresh)
    p.x_range.js_on_change('end', refresh)
    p.y_range.js_on_change('start', refresh)
    p.y_range.js_on_change('end', refresh)

    disable_draw = CustomJS(args={'filter':custom_filter, 'p':p}, code="console.log('disable draw'); filter._may_not_draw = true;")
    enable_draw = CustomJS(args={'filter':custom_filter, 'p':p, 'source':source}, code="console.log('enable draw'); filter._may_not_draw = false; source.change.emit();")

    p.js_on_event(bokeh.events.PanStart, disable_draw)
    p.js_on_event(bokeh.events.PanEnd, enable_draw)

    return custom_filter





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
    r = data.to_numpy()
    ranks = np.arange(len(r))+1
    if filter_pixels:
        ranks, r = pixel_filter(ranks, r, np.log10(ranks), np.log10(r), 1, frame_width, frame_height, (0, np.log10(len(r))), (np.log10(np.min(r)), np.log10(np.max(r))), 1)
    source = ColumnDataSource({'Rank': ranks, 'Reads': r})
    p = figure(x_axis_type="log", y_axis_type="log", x_axis_label="Rank", y_axis_label="Reads", frame_width=frame_width, frame_height=frame_height, **kwargs)

    view = CDSView(filter=make_pixel_filter(p, source, 'Rank', 'Reads', 1.0, 1.0))
    p.scatter('Rank', 'Reads', source=source, view=view)
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
    stats = df.group_by(col).agg([pl.count().alias("count"), pl.col("reads").max()]).select([pl.col("count").max(), pl.col("reads").max()]).collect()
    max_rank = stats["count"][0]
    max_reads = stats["reads"][0]

    sorted_data = df.group_by(col).agg(pl.col("reads").sort(descending=True)).sort(pl.col(col)).collect()
    return max_rank, max_reads, sorted_data


def make_visualisation(df, col, thresholds, outpath):
    max_rank, max_reads, sorted_data = generate_data(df, col)

    ps = []
    download_sources = []
    for sample, data in zip(sorted_data["sample"], sorted_data["reads"]):
        print(sample)
        p = make_ranked(data, title=sample, x_range=(1/2, max_rank*2), y_range=(1/2, max_reads*2), filter_pixels=True)
        download_source = make_threshold(p, max_rank, sample, thresholds)
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

    save_html(column([download_button, grid(ps, ncols=8)]), outpath)


