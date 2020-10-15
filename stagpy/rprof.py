"""Plot radial profiles."""

import matplotlib.pyplot as plt
import numpy as np

from . import conf, misc
from ._step import Rprof
from .stagyydata import StagyyData


def _plot_rprof_list(sdat, lovs, rprofs, stepstr):
    """Plot requested profiles."""
    for vfig in lovs:
        fig, axes = plt.subplots(ncols=len(vfig), sharey=True,
                                 figsize=(4 * len(vfig), 6))
        axes = [axes] if len(vfig) == 1 else axes
        fname = 'rprof_'
        for iplt, vplt in enumerate(vfig):
            xlabel = None
            profs_on_plt = (rprofs[rvar] for rvar in vplt)
            fname += '_'.join(vplt) + '_'
            for ivar, (rprof, rad, meta) in enumerate(profs_on_plt):
                if conf.rprof.depth:
                    rad = rprofs['bounds'][1] - rad
                axes[iplt].plot(rprof, rad,
                                conf.rprof.style,
                                label=meta.description)
                if conf.rprof.depth:
                    axes[iplt].invert_yaxis()
                if xlabel is None:
                    xlabel = meta.kind
                elif xlabel != meta.kind:
                    xlabel = ''
            if ivar == 0:
                xlabel = meta.description
            if xlabel:
                _, unit = sdat.scale(1, meta.dim)
                if unit:
                    xlabel += ' ({})'.format(unit)
                axes[iplt].set_xlabel(xlabel)
            if vplt[0][:3] == 'eta':  # list of log variables
                axes[iplt].set_xscale('log')
            axes[iplt].set_xlim(left=conf.plot.vmin, right=conf.plot.vmax)
            if ivar:
                axes[iplt].legend()
        ylabel = 'Depth' if conf.rprof.depth else 'Radius'
        _, unit = sdat.scale(1, 'm')
        if unit:
            ylabel += ' ({})'.format(unit)
        axes[0].set_ylabel(ylabel)
        misc.saveplot(fig, fname + stepstr)


def plot_grid(step):
    """Plot cell position and thickness.

    The figure is call grid_N.pdf where N is replace by the step index.

    Args:
        step (:class:`~stagpy.stagyydata._Step`): a step of a StagyyData
            instance.
    """
    drad, rad, _ = step.rprofs['dr']
    _, unit = step.sdat.scale(1, 'm')
    if unit:
        unit = ' ({})'.format(unit)
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
    ax1.plot(rad, '-ko')
    ax1.set_ylabel('$r$' + unit)
    ax2.plot(drad, '-ko')
    ax2.set_ylabel('$dr$' + unit)
    ax2.set_xlim([-0.5, len(rad) - 0.5])
    ax2.set_xlabel('Cell number')
    misc.saveplot(fig, 'grid', step.istep)


def plot_average(sdat, lovs):
    """Plot time averaged profiles.

    Args:
        sdat (:class:`~stagpy.stagyydata.StagyyData`): a StagyyData instance.
        lovs (nested list of str): nested list of profile names such as
            the one produced by :func:`stagpy.misc.list_of_vars`.

    Other Parameters:
        conf.core.snapshots: the slice of snapshots.
        conf.conf.timesteps: the slice of timesteps.
    """
    steps_iter = iter(sdat.walk.filter(rprofs=True))
    try:
        step = next(steps_iter)
    except StopIteration:
        return

    sovs = misc.set_of_vars(lovs)

    istart = step.istep
    nprofs = 1
    rprof_averaged = {}
    rads = {}
    metas = {}

    # assume constant z spacing for the moment
    for rvar in sovs:
        rprof, rads[rvar], metas[rvar] = step.rprofs[rvar]
        rprof_averaged[rvar] = np.copy(rprof)

    for step in steps_iter:
        nprofs += 1
        for rvar in sovs:
            rprof_averaged[rvar] += step.rprofs[rvar].values

    ilast = step.istep
    for rvar in sovs:
        # cast to float so that division happens in place
        rprof_averaged[rvar] = Rprof(rprof_averaged[rvar] / nprofs,
                                     rads[rvar], metas[rvar])
    rcmb, rsurf = step.rprofs.bounds
    rprof_averaged['bounds'] = (step.sdat.scale(rcmb, 'm')[0],
                                step.sdat.scale(rsurf, 'm')[0])

    stepstr = '{}_{}'.format(istart, ilast)

    _plot_rprof_list(sdat, lovs, rprof_averaged, stepstr)


def plot_every_step(sdat, lovs):
    """Plot profiles at each time step.

    Args:
        sdat (:class:`~stagpy.stagyydata.StagyyData`): a StagyyData instance.
        lovs (nested list of str): nested list of profile names such as
            the one produced by :func:`stagpy.misc.list_of_vars`.

    Other Parameters:
        conf.core.snapshots: the slice of snapshots.
        conf.conf.timesteps: the slice of timesteps.
    """
    sovs = misc.set_of_vars(lovs)

    for step in sdat.walk.filter(rprofs=True):
        rprofs = {rvar: step.rprofs[rvar] for rvar in sovs}
        rcmb, rsurf = step.rprofs.bounds
        rprofs['bounds'] = (step.sdat.scale(rcmb, 'm')[0],
                            step.sdat.scale(rsurf, 'm')[0])
        stepstr = str(step.istep)

        _plot_rprof_list(sdat, lovs, rprofs, stepstr)


def cmd():
    """Implementation of rprof subcommand.

    Other Parameters:
        conf.rprof
        conf.core
    """
    sdat = StagyyData()

    if conf.rprof.grid:
        for step in sdat.walk.filter(rprofs=True):
            plot_grid(step)

    lovs = misc.list_of_vars(conf.rprof.plot)
    if not lovs:
        return

    if conf.rprof.average:
        plot_average(sdat, lovs)
    else:
        plot_every_step(sdat, lovs)
