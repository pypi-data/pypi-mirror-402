from matplotlib.axes import Axes, SubplotBase
from matplotlib.figure import Figure
from matplotlib import collections, pyplot as plt
import matplotlib as _mpl
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import math
from matplotlib.legend import Legend
import seaborn as _sns
import numpy as np
import matplotlib.patheffects as path_effects


class _axTools(object):

    artistList = (
        mpatches.Wedge,
        mpatches.Ellipse,
        mpatches.Circle,
        mlines.Line2D,
        mlines.Line2D,
        collections.PathCollection,
        collections.PolyCollection,
    )

    def __init__(self) -> None:
        self.color = "#0B0201"

    def __print_values_plot__(self, ax: Axes, x=0, y=0,  value=0, 
                              prefix="", dec=0 , **kwargs):
        if dec == 0:
            data_value = int(value)
        else:
            data_value = np.round(value, dec)
        ax.text(x=x, y=y, s=f"{data_value}{prefix}", **kwargs)

    def __get_orientation__(self, ax: Axes) -> str:
        try:
            if len(ax.containers) > 0:
                my_list = [x.get_height().round(2) for x in ax.containers[0]]
                if all([x == my_list[0] for x in my_list]):
                    orient = "h"
                else:
                    orient = "v"
            else:
                raise ValueError("Tipo de grafico incorrecto")
        except Exception as e:
            raise ValueError(e)
        return orient

    def __get_axes__(self, ax=None):
        if not isinstance(ax, Axes):
            ax = plt.gca()
        return ax

    def __split_to_half_string__(self, input_string):
        words = input_string.split()
        npals = int(len(words) / 2) + 1
        added = True
        modified_words = []
        for i, word in enumerate(words):
            modified_words.append(word)
            if (
                (i + 1) % npals == 0
            ) & added:  # Check if it's the 3rd, 6th, 9th word, etc.
                modified_words.append("\n")
                added = False
            else:
                modified_words.append(" ")
        return "".join(modified_words).strip()

    def show_values_bar(self, ax: None, args={}, **kwargs):
        try:
            axs = self.__get_axes__(ax)
            orient = self.__get_orientation__(axs)
            hist = dict()

            dec = args.get("dec", 3)
            xpad = args.get("xpad", 0)
            ypad = args.get("ypad", 0)
            loc = args.get("loc", "top")
            prefix = args.get("prefix", "")
            min_val = args.get("min_value", -np.inf)
            max_val = args.get("max_value", np.inf)
            
            def set_new_value(value=0):
                if loc == "bottom":
                    new_value = 0
                elif loc == "center":
                    new_value = value / 2
                else:
                    new_value = value
                return new_value

            if orient == "h":
                kwargs["ha"] = kwargs.get("ha", "center")
                kwargs["va"] = kwargs.get("va", "center")
            else:
                kwargs["ha"] = kwargs.get("ha", "center")
                kwargs["va"] = kwargs.get("va", "bottom")

            for i in range(0, len(axs.containers)):
                for bar in axs.containers[i]:
                    height = 0 if math.isnan(bar.get_height()) else bar.get_height()
                    width = 0 if math.isnan(bar.get_width()) else bar.get_width()

                    if orient == "h":
                        if (width>=min_val) and (width<=max_val):
                            pos = bar.get_y()
                            value = set_new_value(width) + hist.get(pos, 0)
                                
                            self.__print_values_plot__(
                                axs,
                                x=value + xpad,
                                y=bar.get_y() + height / 2,
                                dec=dec,
                                value = width,
                                prefix =prefix,
                                **kwargs,
                            )
                            hist[pos] = width + hist.get(pos, 0)

                    else:
                        if (height>=min_val) and (height<=max_val):
                            pos = bar.get_x()
                            value = set_new_value(height) + hist.get(pos, 0)
                                                    
                            self.__print_values_plot__(
                                axs,
                                x=bar.get_x() + width / 2,
                                y=value + ypad,
                                dec=dec,
                                value=height,
                                prefix=prefix,
                                **kwargs,
                            )
                            hist[pos] = height + hist.get(pos, 0)

        except Exception as e:
            raise e

    def get_tickslabel(self, ax=None, axis="x") -> list[str]:
        ax = self.__get_axes__(ax=ax)
        if axis not in ["x", "y"]:
            raise ValueError("El valor de 'axis' debe ser 'x' o 'y'")
        elif axis == "y":
            t = [y.get_text() for y in ax.get_yticklabels()]
        else:
            t = [x.get_text() for x in ax.get_xticklabels()]
        return t

    def set_tickslabel(self, ax=None, args: dict = {}, **kwargs) -> Axes:

        axis = args.get("axis", "x")
        visible = args.get("visible", True)
        labels: list = args.get("labels", [])
        rotation: int = args.get("rotation", 0)
        loc = args.get("loc", "default")
        bgcolors: list = args.get("bgcolors", [])
        shadow_line = args.get("shadow_line", 0)
        shadow_color = args.get("shadow_color", self.color)

        ax = self.__get_axes__(ax=ax)
        fig = ax.get_figure()

        if axis in ["x", "y"]:
            if visible == False:
                if axis == "x":
                    ax.xaxis.set_visible(False)
                elif axis == "y":
                    ax.yaxis.set_visible(False)
                return ax

            if axis == "x":
                ticklabels = ax.get_xticklabels()
                ax.xaxis.set_ticks_position(loc)
            elif axis == "y":
                ticklabels = ax.get_yticklabels()
                ax.yaxis.set_ticks_position(loc)

            labels_ax = [t.get_text() for t in ticklabels]

            if isinstance(labels, list):
                if labels:
                    del labels[len(ticklabels) :]
                    for i in [*range(0, len(labels))]:
                        labels_ax[i] = labels[i]
            elif isinstance(labels, dict):
                for i, v in zip(labels.keys(), labels.values()):
                    labels_ax[i] = v

            if len(bgcolors) > 0:
                del bgcolors[len(ticklabels) :]
                bbox = dict(boxstyle="square", alpha=0.3)
                for i, c in enumerate(bgcolors):
                    ticklabels[i].set_bbox(bbox)
                    ticklabels[i].set_backgroundcolor(c)

            if axis == "x":
                ax.xaxis.set_ticks(
                    [l.get_position()[0] for l in ticklabels],
                    labels=labels_ax,
                    rotation=rotation,
                    **kwargs,
                )

            elif axis == "y":
                ax.yaxis.set_ticks(
                    [l.get_position()[1] for l in ticklabels],
                    labels=labels_ax,
                    rotation=rotation,
                    **kwargs,
                )

            if shadow_line > 0:
                effects = [
                    path_effects.Stroke(
                        linewidth=shadow_line,
                        foreground=shadow_color,
                        alpha=0.8,
                    ),
                    path_effects.Normal(),
                ]
                for t in ticklabels:
                    t.set_path_effects(effects)
        else:
            raise ValueError("axis value {0} is not available".format(axis))

        return ax

    def theme(
        self,
        op: str = "spine",
        top: bool = False,
        right: bool = False,
        left: bool = False,
        bottom: bool = False,
        despine_trim: bool = False,
        despine_offset: int = 0,
        spine_butt="left",
        ax=None,
    ):
        ax = self.__get_axes__(ax=ax)
        options = ["despine", "spine", "clear"]
        if not op in options:
            raise ValueError("Value is not in '{0}'".format(options))

        if op == options[0]:
            _sns.despine(
                top=top,
                right=right,
                left=left,
                bottom=bottom,
                trim=despine_trim,
                offset=despine_offset,
            )

        elif op == options[1]:
            ax.spines["left"].set_visible(left)
            ax.spines["top"].set_visible(top)
            ax.spines["bottom"].set_visible(bottom)
            ax.spines["right"].set_visible(right)
            ax.spines[spine_butt].set_linewidth(1.5)
            ax.spines[spine_butt].set_capstyle("butt")

        elif op == options[2]:
            orient = self.__get_orientation__(ax=ax)
            _sns.despine(
                top=True, bottom=True, right=True, left=True, trim=True, offset=3
            )
            if orient == "v":
                ax.get_yaxis().set_visible(False)
            elif orient == "h":
                ax.get_xaxis().set_visible(False)
            ax.set_xlabel("")
            ax.set_ylabel("")

        else:
            _sns.despine(top=True, bottom=False, right=False, left=False, trim=False)

        return ax

    def set_title(
        self, ax=None, title: str = str(), loc: str = "left", args: dict = {}, **kwargs
    ) -> None:

        if loc == "center":
            pos = 0.5
        elif loc == "left":
            pos = 0.0
        elif loc == "right":
            pos = 0.96
        else:
            pos = 0.0
            loc = "left"

        if ax is None:
            ax = self.__get_axes__(ax=ax)

        # Check if set figure or Axesplot
        if isinstance(ax, SubplotBase):
            ax = self.__get_axes__(ax=ax)
            ax.set_title(
                label=title,
                x=pos + args.get("xpad", 0),
                y=1.05 + args.get("ypad", 0),
                verticalalignment="bottom",
                horizontalalignment=loc,
                **kwargs,
            )

        elif isinstance(ax, Figure):
            plt.suptitle(
                title,
                y=1 + args.get("ypad", 0),
                x=pos + args.get("xpad", 0),
                verticalalignment="bottom",
                horizontalalignment=loc,
                **kwargs,
            )

    def set_subtitle(
        self,
        ax=None,
        subtitle: str = str(),
        loc: str = "left",
        args: dict = {},
        **kwargs,
    ) -> None:
        ax = self.__get_axes__(ax=ax)

        ad = 0.04 if (isinstance(ax, Figure)) else 0
        if loc == "center":
            pos = 0.50
        elif loc == "left":
            pos = 0 + ad
        elif loc == "right":
            pos = 1 - ad
        else:
            pos = 0.048
            loc = "left"

        if isinstance(ax, SubplotBase):
            txt = ax.text(
                x=pos + args.get("xpad", 0),
                y=1.02 + args.get("ypad", 0),
                s=subtitle,
                transform=ax.transAxes,
                horizontalalignment=loc,
                verticalalignment="bottom",
                **kwargs,
            )

        elif isinstance(ax, Figure):
            ax.text(
                s=subtitle,
                x=pos + args.get("xpad", 0),
                y=1 + args.get("ypad", 0),
                horizontalalignment=loc,
                verticalalignment="bottom",
                **kwargs,
            )

    def set_legend(
        self,
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
        **kwargs,
    ) -> Legend:

        legend = None

        if type(loc) is tuple:
            bbox_to_anchor = loc
            loc = 0
        else:
            bbox_to_anchor = None

        if label_fontsize is None:
            label_fontsize = _mpl.rcParams["legend.fontsize"]
        if title_fontsize is None:
            title_fontsize = _mpl.rcParams["legend.fontsize"]

        propF = {"weight": "normal", "size": label_fontsize}
        kwargs["loc"] = loc
        kwargs["alignment"] = title_loc
        kwargs["title_fontsize"] = title_fontsize
        kwargs["ncol"] = ncols
        if "borderpad" not in kwargs:
            kwargs["borderpad"] = 0.82

        if not isinstance(ax, Figure):
            ax = self.__get_axes__(ax=ax)

            if show:
                leg = ax.get_legend()
                leg = ax.legend(["Graph 1"]) if leg is not None else leg

                if title == "" and leg is not None:
                    title = leg.get_title().get_text()
                    title = title.capitalize()

                if leg is not None:
                    leg.set_title(title)

                if handles is None or labels is None:
                    handles1, legs1 = ax.get_legend_handles_labels()
                    handles = handles1 if handles is None else handles
                    labels = legs1 if labels is None else labels
                    for h, l in zip(handles, labels):
                        h.set_label(l)
            else:
                # Remove legend
                l = ax.get_legend()
                if l is not None:
                    l.remove()
        else:
            axs = list()
            loc = 8 if loc == 0 else loc

            if ax is None:
                axs = ax.axes
            else:
                if isinstance(ax, list):
                    axs.extend(ax)
                else:
                    axs.append(ax)
                for a in ax.axes:
                    leg = a.legend(["Graph 1"])
                    leg.remove()

            handles, legs = list(), list()
            ax.legends = []
            for a in axs:
                h, l = a.get_legend_handles_labels()
                handles.extend(h)
                legs.extend(l)
            legs = labels if labels is not None else legs

        legend = ax.legend(
            title=title,
            handles=handles,
            prop=propF,
            labels=labels,
            bbox_to_anchor=bbox_to_anchor,
            **kwargs,
        )
        return legend

    def set_alpha(self, ax=None, alpha: float = 1.0):
        if ax is not None:
            if isinstance(ax, Axes):
                ch = ax.get_children()
                for c in ch:
                    if isinstance(c, _axTools.artistList):
                        c.set_alpha(alpha)
                    elif isinstance(c, mpatches.Rectangle):
                        """All rectangles and not background rectangle"""
                        if (
                            not float(c.get_width()) == 1.0
                            and not float(c.get_height()) == 1.0
                        ):
                            c.set_alpha(alpha)
