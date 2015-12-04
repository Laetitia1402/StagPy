"""Plots radial profiles coming out of stagyy.

Author: Stephane Labrosse with inputs from Martina Ulvrova and Adrien Morison
Date: 2015/09/11
"""
import numpy as np
import matplotlib.pyplot as plt
import f90nml
import os
import sys
import seaborn as sns

def rprof_cmd(args):
    '''
    Function to plot radial profiles
    '''
    if args.xkcd:
        plt.xkcd()

    istart, ilast, istep = args.timestep

    ############### INPUT PARAMETERS ################
    # should rather be default parameters to be replaced by command line options

    plot_grid = True
    plot_temperature = True
    plot_minmaxtemp = False
    plot_velocity = True
    plot_minmaxvelo = False
    plot_viscosity = False
    plot_minmaxvisco = False
    plot_advection = True
    plot_energy = True
    plot_concentration = True
    plot_minmaxcon = False
    plot_conctheo = True
    plot_overturn_init = True

    linestyles = ('-', '--', '-.', ':')
    lwdth = args.linewidth
    ftsz = args.fontsize

    # parameters for the theoretical composition profiles
    rmin = 1.19
    rmax = rmin + 1.

    #Read par file in the parent or present directory.
    # should be a separated func in misc module
    read_par_file = True
    if os.path.exists('../par'):
        par_file = '../par'
    elif os.path.exists('par'):
        par_file = 'par'
    else:
        print 'No par file found. Input pars by hand'
        read_par_file = False
        rcmb = 1
        geom = str(raw_input('spherical (s) or cartesian (c)? '))
        spherical = geom == 's'

    if read_par_file:
        nml = f90nml.read(par_file)
        spherical = (nml['geometry']['shape'] == 'spherical' or
                     nml['geometry']['shape'] == 'Spherical')
        if spherical:
            rcmb = nml['geometry']['r_cmb']
        else:
            rcmb = 0.
        stem = nml['ioin']['output_file_stem']
        ste = stem.split('/')[-1]
#        proffile = ste+'_rprof.dat'
        if os.path.exists('../'+ste+'_rprof.dat'):
            proffile = '../'+ste+'_rprof.dat'
        elif os.path.exists(ste+'_rprof.dat'):
            proffile = ste+'_rprof.dat'
        elif os.path.exists(stem+'_rprof.dat'):
            proffile = stem+'_rprof.dat'
        else:
            print 'No profile file found. stem = ', ste
            sys.exit()

        rmin = rcmb
        rmax = rcmb+1
        if plot_conctheo:
            if 'fe_eut' in nml['tracersin']:
                xieut = nml['tracersin']['fe_eut']
            else:
                xieut = 0.8
            if 'k_fe' in nml['tracersin']:
                k_fe = nml['tracersin']['k_fe']
            else:
                k_fe = 0.85
            if 'fe_cont' in nml['tracersin']:
                xi0l = nml['tracersin']['fe_cont']
            else:
                xi0l = 0.1
            xi0s = k_fe*xi0l
            xired = xi0l/xieut
            rsup = (rmax**3-xired**(1/(1-k_fe))*(rmax**3-rmin**3))**(1./3.)

            def initprof(rpos):
                """Theoretical initial profile."""
                if rpos < rsup:
                    return xi0s*((rmax**3-rmin**3)/(rmax**3-rpos**3))**(1-k_fe)
                else:
                    return xieut

    timesteps = []
    data0 = []
    lnum = -1
    fich = open(proffile)
    for line in fich:
        if line != '\n':
            lnum = lnum+1
            lll = ' '.join(line.split())
            if line[0] == '*':
                timesteps.append([lnum, int(lll.split(' ')[1]),
                                  float(lll.split(' ')[5])])
            else:
                llf = np.array(lll.split(' '))
                data0.append(llf)

    tsteps = np.array(timesteps)
    nsteps = tsteps.shape[0]
    data = np.array(data0)
    if ilast == -1:
        ilast = nsteps-1
    if istart == -1:
        istart = nsteps-1

    nzp = []
    for iti in range(0, nsteps-1):
        nzp = np.append(nzp, tsteps[iti+1, 0]-tsteps[iti, 0]-1)

    nzp = np.append(nzp, lnum-tsteps[nsteps-1, 0])

    nzs = [[0, 0, 0]]
    nzc = 0
    for iti in range(1, nsteps):
        if nzp[iti] != nzp[iti-1]:
            nzs.append([iti, iti-nzc, int(nzp[iti-1])])
            nzc = iti
    if nzp[nsteps-1] != nzs[-1][1]:
        nzs.append([nsteps, nsteps-nzc, int(nzp[nsteps-1])])

    nzi = np.array(nzs)

    def calc_energy(ir0, ir1):
        """
        Computes the energy balance as function of radial distance
        """
        zgrid = np.array(data[ir0:ir1, 63], float)
        zgrid = np.append(zgrid, 1.)
        dzg = np.array(data[ir0+1:ir1, 0], float) - np.array(data[ir0:ir1-1, 0],
                                                             float)
        qadv = np.array(data[ir0:ir1-1, 60], float)
        qadv = np.insert(qadv, 0, 0.)
        qadv = np.append(qadv, 0.)
        qcond = (np.array(data[ir0:ir1-1, 1], float) -
                 np.array(data[ir0+1:ir1, 1], float))/dzg
        qcond0 = (1.-float(data[ir0, 1]))/float(data[ir0, 0])
        qtop = float(data[ir1, 1])/(1.-float(data[ir1, 0]))
        qcond = np.insert(qcond, 0, qcond0)
        qcond = np.append(qcond, qtop)
        qtot = qadv+qcond
        return qtot, qadv, qcond, zgrid


    def plotprofiles(quant, *vartuple, **kwargs):
        """Plot the chosen profiles for the chosen timesteps

        quant holds the strings for the x axis annotation and
        the legends for the additional profiles

        vartuple contains the numbers of the column to be plotted

        A kwarg should be used for different options, e.g. whether
        densities of total values are plotted
        """
        if kwargs != {}:
            for key, value in kwargs.iteritems():
                if key == 'integrated':
                    integrate = value
                else:
                    print "kwarg value not understood %s == %s" %(key, value)
                    print "ignored"
        else:
            integrate = False

        if integrate:
            integ = lambda f, r: f * (r/rmax)**2

        if quant[0] == 'Grid':
            fig, axe = plt.subplots(2, sharex=True)
        else:
            fig, axe = plt.subplots()

        timename = str(istart) + "_" + str(ilast) + "_" + str(istep)

        for step in range(istart, ilast, istep):
            step = step +1# starts at 0=> 15 is the 16th
            # find the indices
            ann = sorted(np.append(nzi[:, 0], step))
            inn = ann.index(step)
            nnz = np.multiply(nzi[:, 1], nzi[:, 2])

            ir0 = np.sum([nnz[0:inn]])+(step-nzi[inn-1, 0]-1)*nzi[inn, 2]
            ir1 = ir0+nzi[inn, 2]-1

            if quant[0] == 'Energy':
                energy = calc_energy(ir0, ir1)

            #Plot the profiles
            if quant[0] == 'Grid':
                axe[0].plot(data[ir0:ir1, 0], '-ko', label='z')
                axe[0].set_ylabel('z', fontsize=ftsz)

                dzgrid = (np.array(data[ir0+1:ir1, 0], np.float) -
                          np.array(data[ir0:ir1-1, 0], np.float))
                axe[1].plot(dzgrid, '-ko', label='dz')
                axe[1].set_xlabel('cell number', fontsize=ftsz)
                axe[1].set_ylabel('dz', fontsize=ftsz)
            else:
                if quant[0] == 'Energy':
                    profiles = np.array(np.transpose(energy)[:, [0, 1, 2]],
                                        float)
                    radius = np.array(np.transpose(energy)[:, 3], float) + rcmb
                else:
                    profiles = np.array(data[ir0:ir1, vartuple], float)
                    radius = np.array(data[ir0:ir1, 0], float) + rcmb
                for i in range(profiles.shape[1]):
                    if integrate:
                        donnee = map(integ, profiles[:, i], radius)
                    else:
                        donnee = profiles[:, i]
                    if i == 0:
                        pplot = plt.plot(donnee, radius, linewidth=lwdth,
                                         label=r'$t=%.2e$' %
                                         (tsteps[step-1, 2]))

                        # get color and size characteristics
                        col = pplot[0].get_color()

                        # plot the overturned version of the initial profiles
                        if ((quant[0] == 'Concentration' or
                             quant[0] == 'Temperature') and
                                plot_overturn_init and step == istart+1):
                            rfin = (rmax**3.+rmin**3.-radius**3.)**(1./3.)
                            plt.plot(donnee, rfin, '--', c=col,
                                     linewidth=lwdth, label='Overturned')

                        # plot the theoretical initial profile and its
                        # overturned version
                        if (quant[0] == 'Concentration' and
                                plot_conctheo and step == istart+1):
                            cinit = map(initprof, radius)
                            rfin = (rmax**3.+rmin**3.-radius**3.)**(1./3.)
                            plt.plot(cinit, radius, 'r--',
                                     linewidth=lwdth, label='Theoretical')
                            plt.plot(cinit, rfin, 'r-.',
                                     linewidth=lwdth, label='Overturned')

                    else:
                        # additional plots (e. g. min, max)
                        plt.plot(donnee, radius, c=col, dash_capstyle='round',
                                 linestyle=linestyles[i], linewidth=lwdth)
                    # change the vertical limits
                    plt.ylim([rmin-0.05, rmax+0.05])
                if len(vartuple) > 1 and step == ilast:
                        # legends for the additionnal profiles
                    axes = plt.gca()
                    rangex = axes.get_xlim()
                    rangey = axes.get_ylim()
                    xlgd1 = rangex[1]-0.12*(rangex[1]-rangex[0])
                    xlgd2 = rangex[1]-0.05*(rangex[1]-rangex[0])
                    for i in range(profiles.shape[1]):
                        ylgd = rangey[1]-0.05*(i+1)*(rangey[1]-rangey[0])
                        plt.plot([xlgd1, xlgd2], [ylgd, ylgd], c='black',
                                 linestyle=linestyles[i], linewidth=lwdth,
                                 dash_capstyle='round',)
                        plt.text(xlgd1-0.02*(rangex[1]-rangex[0]), ylgd,
                                 quant[i+1], ha='right')

                    plt.xlabel(quant[0], fontsize=ftsz)
                    plt.ylabel('z', fontsize=ftsz)
                    plt.xticks(fontsize=ftsz)
                    plt.yticks(fontsize=ftsz)
        if quant[0] == 'Grid':
            plt.savefig("Grid" + timename + ".pdf", format='PDF')
        else:
            # legend
            lgd = plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                             borderaxespad=0., mode="expand",
                             ncol=3, fontsize=ftsz,
                             columnspacing=1.0, labelspacing=0.0,
                             handletextpad=0.1, handlelength=1.5,
                             fancybox=True, shadow=False)

            plt.savefig(quant[0].replace(' ', '_')+timename+".pdf",
                        format='PDF',
                        bbox_extra_artists=(lgd, ), bbox_inches='tight')
        plt.close(fig)
        return

    # Now use it for the different types of profiles

    if plot_temperature:
        if plot_minmaxtemp:
            plotprofiles(['Temperature', 'Mean', 'Minimum', 'Maximum'], 1, 2, 3,
                         integrated=False)
        else:
            plotprofiles(['Temperature'], 1)

    if plot_velocity:
        if plot_minmaxvelo:
            plotprofiles(['Vertical Velocity', 'Mean', 'Minimum', 'Maximum'],
                         7, 8, 9)
        else:
            plotprofiles(['Vertical Velocity'], 7)

    if plot_viscosity:
        if plot_minmaxvisco:
            plotprofiles(['Viscosity', 'Mean', 'Minimum', 'Maximum'],
                         13, 14, 15)
        else:
            plotprofiles(['Viscosity'], 13)

    if plot_concentration:
        if plot_minmaxcon:
            plotprofiles(['Concentration', 'Mean', 'Minimum', 'Maximum'],
                         36, 37, 38)
        else:
            plotprofiles(['Concentration'], 36)

    # Plot grid spacing
    if plot_grid:
        plotprofiles(['Grid'])

    # Plot the profiles of vertical advection: total and contributions from up-
    # and down-welling currents
    if plot_advection:
        plotprofiles(['Advection per unit surface', 'Total', 'down-welling',
                      'Up-welling'], 57, 58, 59)
        if spherical:
            plotprofiles(['Total scaled advection', 'Total', 'down-welling',
                          'Up-welling'], 57, 58, 59, integrated=True)
    if plot_energy:
        plotprofiles(['Energy', 'Total', 'Advection',
                      'conduction'], 57, 58, 59, integrated=True)
