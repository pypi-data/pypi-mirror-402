import numpy as np
from ._ax_functions import _axTools

__axf__ = _axTools()


def show_values(
    ax=None,
    kind="bar",
    dec=3,
    loc="top",
    prefix: str = "",
    min_value=-np.inf,
    max_value=np.inf,
    xpad: float = 0,
    ypad: float = 0,
    kw_args={},
):
    args = {"dec": dec, "xpad": xpad, "ypad": ypad, "loc": loc, "prefix": prefix,
            "min_value":min_value, "max_value": max_value}

    if kind == "bar":
        __axf__.show_values_bar(ax=ax, args=args, **kw_args)
    else:
        print(f"show_values: kind '{kind}' aun no soportado")


def get_tickslabel(ax=None, axis="x") -> list[str]:
    return __axf__.get_tickslabel(ax=ax, axis=axis)


def set_tickslabel(
    ax=None,
    axis="x",
    visible=True,
    labels: list = [],
    rotation=0,
    loc="default",
    bgcolors=None,
    shadow_line=None,
    shadow_color=None,
    kw_args={},
):

    args = {
        "axis": axis,
        "visible": visible,
        "labels": labels,
        "rotation": rotation,
        "loc": loc,
        "bgcolors": bgcolors,
    }

    if shadow_line is not None:
        args["shadow_line"] = shadow_line

    if shadow_color is not None:
        args["shadow_color"] = shadow_color

    return __axf__.set_tickslabel(ax=ax, args=args, **kw_args)


def theme(
    ax=None,
    op: str = "spine",
    top: bool = False,
    right: bool = False,
    left: bool = False,
    bottom: bool = False,
    despine_trim: bool = False,
    despine_offset: int = 0,
    spine_butt="left",
):
    return __axf__.theme(
        op=op,
        top=top,
        right=right,
        left=left,
        bottom=bottom,
        despine_trim=despine_trim,
        despine_offset=despine_offset,
        spine_butt=spine_butt,
        ax=ax,
    )


def set_title(
    ax=None,
    title: str = "",
    loc: str = "center",
    xpad: float = 0.0,
    ypad: float = 0.0,
    kw_args={},
):
    args = {
        "xpad": xpad,
        "ypad": ypad,
    }

    return __axf__.set_title(ax=ax, title=title, loc=loc, args=args, **kw_args)


def set_subtitle(
    ax=None,
    subtitle: str = "",
    loc: str = "left",
    xpad: float = 0.0,
    ypad: float = 0.0,
    kw_args={},
):
    args = {
        "xpad": xpad,
        "ypad": ypad,
    }

    return __axf__.set_subtitle(
        ax=ax, subtitle=subtitle, loc=loc, args=args, **kw_args
    )


def set_legend(
    ax=None,
    show: bool = True,
    title="",
    title_loc: str = "left",
    ncols: int = 1,
    loc="best",
    title_fontsize=None,
    label_fontsize=None,
    labels: list = [],
    handles: list = [],
    borderpad=0.82,
    kw_args={},
):
    return __axf__.set_legend(
        ax=ax,
        show=show,
        title=title,
        title_loc=title_loc,
        ncols=ncols,
        loc=loc,
        title_fontsize=title_fontsize,
        label_fontsize=label_fontsize,
        labels=labels,
        handles=handles,
        borderpad=borderpad,
        **kw_args,
    )


def set_alpha(ax=None, alpha=1.0):
    return __axf__.set_alpha(ax=ax, alpha=alpha)
