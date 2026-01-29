from Bio import Phylo
import copy
from yxtree.src.tree import lookup_by_names, get_ancestors, get_path_step, add_clade_name

import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

from matplotlib import rcParams
rcParams['font.family'] = 'Arial'

rcParams['mathtext.it'] = 'Arial'
rcParams['mathtext.rm'] = 'Arial'
rcParams['mathtext.tt'] = 'Arial'
rcParams['mathtext.bf'] = 'Arial'
rcParams['mathtext.cal'] = 'Arial'
rcParams['mathtext.sf'] = 'Arial'
rcParams['mathtext.fontset'] = 'custom'

DEFAULT_STYLE_PARAMS = {
    # clade lines
    'bg_color': 'gray',
    'bg_lw': 0.5,
    'clade_colors': {},
    'clade_labels': {},
    'clade_lw': {},
    'equal_tip_length': False,
    # tip labels
    'tip_label': False,
    'tip_fontsize': 6,
    'tip_color': {},
    'tip_bg_color': 'black',
    'tip_ha': 'right',
    'tip_va': 'center',
    # tree
    'use_edge_length': True,
    # zoom
    'zoom_target_size': None,
    # fig
    'fig_size': None,
}


class RectTreePlotter:
    def __init__(self, tree, **kwargs):
        self.tree = copy.deepcopy(tree)

        # Set default style parameters
        self.style_params = DEFAULT_STYLE_PARAMS

        # Update style parameters
        self.style_params.update(kwargs)

    def plot(self, ax=None, save_file=None, **kwargs):
        # Set style parameters
        style_params = copy.deepcopy(self.style_params)
        style_params.update(kwargs)

        if not hasattr(self, 'coord_dict'):
            self.calculate_coordinates(style_params['use_edge_length'],
                                       style_params['equal_tip_length'])
        if style_params['zoom_target_size']:
            self.zoomer(style_params['zoom_target_size'])

        xlim = (min([x for x, y in self.coord_dict.values()]) - 0.02 * max([x for x, y in self.coord_dict.values()]),
                    max([x for x, y in self.coord_dict.values()]) + 0.02 * max([x for x, y in self.coord_dict.values()]))
        ylim = (min([y for x, y in self.coord_dict.values()]) - 0.02 * max([y for x, y in self.coord_dict.values()]),
                    max([y for x, y in self.coord_dict.values()]) + 0.02 * max([y for x, y in self.coord_dict.values()]))

        # Plot the tree
        if ax is None:
            if style_params['fig_size']:
                fig_size = style_params['fig_size']
            else:
                x = 10
                y = (ylim[1] - ylim[0]) * 0.05
                fig_size = (x, y)
            fig, ax = plt.subplots(figsize=fig_size)
            # fig, ax = plt.subplots()
            # ax.set_aspect('equal')
            ax.axis('off')

        plot_clade(self.tree, self.coord_dict, ax, style_params)

        ax.set_xlim(xlim[0], xlim[1])
        ax.set_ylim(ylim[0], ylim[1])

        if save_file:
            fig.savefig(save_file, format='pdf', facecolor='none',
                        edgecolor='none', bbox_inches='tight')
        else:
            plt.show()

    def calculate_coordinates(self, use_edge_length=True, equal_tip_length=False):
        self.tree, self.coord_dict = calculate_coordinates(
            self.tree, use_edge_length, equal_tip_length)

    def zoomer(self, target_size):
        self.coord_dict = coord_zoom(self.coord_dict, target_size)


def get_distance_to_root(A, tree, use_edge_length=True):
    """
    get distance (sum of branch length) from given clade to root
    """
    ancest_list = get_ancestors(A, tree) + [A]
    distance = 0.0
    for i in ancest_list:
        if use_edge_length:
            distance = distance + i.branch_length if i.branch_length else 0
        else:
            distance = distance + 1
    return distance


def calculate_coordinates(tree, use_edge_length=True, equal_tip_length=False):
    """
    return coord_dict which include every clade's coord in the tree. The X is the branch value, and the Y is base on leaf number.
    """
    coord_dict = {}

    # get X axis aka branch length from root to clade
    tree = add_clade_name(tree)
    tree_name_dir = lookup_by_names(tree, order='preorder')

    for clade_name in tree_name_dir:
        X_clade = get_distance_to_root(
            tree_name_dir[clade_name], tree, use_edge_length)
        # tree_name_dir[clade_name].rela_coord = (X_clade, None)
        coord_dict[clade_name] = (X_clade, None)

    # get Y axis
    # first for leaf
    order_leaf_list = [
        clade_name for clade_name in tree_name_dir if tree_name_dir[clade_name].is_terminal()]
    for leaf_name in order_leaf_list:
        # X_clade, Y_clade = tree_name_dir[leaf_name].rela_coord
        X_clade, Y_clade = coord_dict[leaf_name]
        if (X_clade is None) or (not Y_clade is None):
            raise ValueError("clade's coord is already set")
        # Y_clade = float(order_leaf_list.index(leaf_name))
        Y_clade = len(order_leaf_list) - order_leaf_list.index(leaf_name) - 1
        # tree_name_dir[leaf_name].rela_coord = (X_clade, Y_clade)
        coord_dict[leaf_name] = (X_clade, Y_clade)

    # for orther clade, we should cal node which close to leaf
    path_for_target_to_most_far_leaf_dict = {}
    for clade_name in tree_name_dir:
        if clade_name in order_leaf_list:
            continue
        else:
            most_far_path = max([get_path_step(leaf_tmp, tree_name_dir[clade_name], tree) for leaf_tmp in
                                 tree_name_dir[clade_name].get_terminals()])
            if most_far_path not in path_for_target_to_most_far_leaf_dict:
                path_for_target_to_most_far_leaf_dict[most_far_path] = []
            path_for_target_to_most_far_leaf_dict[most_far_path].append(
                clade_name)

    for i in sorted(path_for_target_to_most_far_leaf_dict.keys()):
        for clade_name in path_for_target_to_most_far_leaf_dict[i]:
            # X_clade, Y_clade = tree_name_dir[clade_name].rela_coord
            X_clade, Y_clade = coord_dict[clade_name]
            # son_Y = [son.rela_coord[1] for son in tree_name_dir[clade_name]]
            son_Y = [coord_dict[son.name][1]
                     for son in tree_name_dir[clade_name].clades]
            Y_clade = (max(son_Y) - min(son_Y)) / 2 + min(son_Y)
            # tree_name_dir[clade_name].rela_coord = (X_clade, Y_clade)
            coord_dict[clade_name] = (X_clade, Y_clade)

    # Adjust leaf nodes' X coordinate to be equal if equal_tip_length is True
    if equal_tip_length:
        max_x = max(coord_dict[leaf_name][0] for leaf_name in order_leaf_list)
        for leaf_name in order_leaf_list:
            coord_dict[leaf_name] = (max_x, coord_dict[leaf_name][1])

    # return tree
    return tree, coord_dict


def coord_zoom(coord_dict, target_size):
    rela_x_list = [x for x, y in coord_dict.values()]
    rela_y_list = [y for x, y in coord_dict.values()]
    rela_fig_size = (min(rela_x_list), max(rela_x_list),
                     min(rela_y_list), max(rela_y_list))

    zoomed_coord_dict = {
        clade_name: zoomer(coord_dict[clade_name], target_size, rela_fig_size) for clade_name in
        coord_dict}

    return zoomed_coord_dict


def zoomer(a_point_coord, target_size, raw_size, blank=(0, 0, 0, 0), reverse_x=False, reverse_y=False):
    """
    scale a point in a raw size to a new size

    point = (0,0)
    raw_size = (-2,2,-2,2) # x leaf,x right, y tail,y head

    target_size = (0,20,0,100)
    new point = (10,50)

    """

    b_x_L, b_x_R, b_y_T, b_y_H = blank
    a_x_L, a_x_R, a_y_T, a_y_H = target_size
    w_x_L, w_x_R, w_y_T, w_y_H = a_x_L + b_x_L, a_x_R - \
        b_x_R, a_y_T + b_y_T, a_y_H - b_y_H
    r_x_L, r_x_R, r_y_T, r_y_H = raw_size

    if reverse_x:
        o_x = w_x_R - (a_point_coord[0] - r_x_L) / \
            (r_x_R - r_x_L) * (w_x_R - w_x_L)
    else:
        o_x = (a_point_coord[0] - r_x_L) / \
            (r_x_R - r_x_L) * (w_x_R - w_x_L) + w_x_L

    if reverse_y:
        o_y = w_y_H - (a_point_coord[1] - r_y_T) / \
            (r_y_H - r_y_T) * (w_y_H - w_y_T)
    else:
        o_y = (a_point_coord[1] - r_y_T) / \
            (r_y_H - r_y_T) * (w_y_H - w_y_T) + w_y_T

    return o_x, o_y


# def line_segment_plot(ax, start, end, facecolor='w', lw=2):
#     verts = [start, end]
#     codes = [mpath.Path.MOVETO, mpath.Path.LINETO]

#     path = mpath.Path(verts, codes)
#     patch = mpatches.PathPatch(path, facecolor=facecolor, lw=lw)
#     ax.add_patch(patch)


def plot_clade(tree, coord_dict, ax, style_params):
    tree_name_dict = lookup_by_names(tree, 'level')
    for clade_name in tree_name_dict:
        clade_tmp = tree_name_dict[clade_name]
        son_clade = clade_tmp.clades
        son_y = []
        for son_clade_tmp in son_clade:
            son_color = style_params['clade_colors'].get(
                son_clade_tmp.name, style_params['bg_color'])
            son_lw = style_params['clade_lw'].get(
                son_clade_tmp.name, style_params['bg_lw'])
            if son_clade_tmp.name in style_params['clade_colors']:
                print(son_clade_tmp.name, son_color, son_lw)
            # line_segment_plot(ax, (coord_dict[son_clade_tmp.name][0], coord_dict[son_clade_tmp.name][1]),
            #                   (coord_dict[clade_tmp.name][0], coord_dict[son_clade_tmp.name][1]), son_color, son_lw)
            ax.plot([coord_dict[son_clade_tmp.name][0], coord_dict[clade_tmp.name][0]], [
                    coord_dict[son_clade_tmp.name][1], coord_dict[son_clade_tmp.name][1]], color=son_color, lw=son_lw)            
            son_y.append(coord_dict[son_clade_tmp.name][1])

        color = style_params['clade_colors'].get(
            clade_name, style_params['bg_color'])
        lw = style_params['clade_lw'].get(clade_name, style_params['bg_lw'])

        if not clade_tmp.is_terminal():
            if clade_name in style_params['clade_colors']:
                print(clade_name, color, lw)
            # line_segment_plot(ax, (coord_dict[clade_tmp.name][0], min(
            #     son_y)), (coord_dict[clade_tmp.name][0], max(son_y)), color, lw)
            ax.plot([coord_dict[clade_tmp.name][0], coord_dict[clade_tmp.name][0]], [
                    min(son_y), max(son_y)], color=color, lw=lw)
    # Annotate the leaf nodes
    tip_label = style_params.get('tip_label', True)
    if tip_label == True:
        for clade in coord_dict:
            if tree_name_dict[clade].is_terminal():
                tip_color = style_params['tip_color'].get(
                    tree_name_dict[clade].name, style_params['bg_color'])
                ax.text(coord_dict[tree_name_dict[clade].name][0], coord_dict[tree_name_dict[clade].name][1], tree_name_dict[clade].name, ha=style_params['tip_ha'],
                        va=style_params['tip_va'], fontsize=style_params['tip_fontsize'], color=tip_color)


# if __name__ == '__main__':
#     tree = Phylo.read('yxtree/data/tree.nwk', 'newick')
#     plotter = RectTreePlotter(tree)
#     plotter.plot()
