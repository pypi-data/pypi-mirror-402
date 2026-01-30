from astropy.coordinates import SkyCoord, name_resolve
import astropy.units as u
from astroquery.gaia import Gaia
Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
Gaia.ROW_LIMIT = 2000 #max for async searches

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# #########
#  * * * * 
# #########

def objloc(obj):
	"""
	Get object location.

	Parameters:
		obj (str): Name or coordinates for object of interest. If coordinates, should be in
			HH:MM:SS DD:MM:SS or degree formats. Names must be resolvable in SIMBAD.
	Returns:
		coords (astropy coordinates object)
	"""
	isname = False #check if obj is name or coordinates
	for s in obj:
		if s.isalpha():
			isname = True
			break

	if isname:
		try: 
		#simbad should be most reliable and should be queried first
		#seems astropy changed recently, though because I've seen funky behavior
			name_resolve.sesame_database.set('simbad')
			coords = name_resolve.get_icrs_coordinates(obj)
		except:
		#if no simbad results, THEN query other databses for coordinates
			name_resolve.sesame_database.set('all')
			coords = name_resolve.get_icrs_coordinates(obj)

	if not isname:
		if ':' in obj:
			coords = SkyCoord(obj, unit = (u.hour, u.deg), frame = 'icrs')
		if not ':' in obj:
			coords = SkyCoord(obj, unit = u.deg, frame = 'icrs')

	return coords


def select(obj, aper, pmra = None, pmd = None, pmthresh = 0.5):
	"""
	Select stars from Gaia to include in CMD.

	Parameters:
		obj (str): Name or coordinates for object of interest. If coordinates, should be in
			HH:MM:SS DD:MM:SS or degree formats. Names must be resolvable in SIMBAD.
		aper (float): Radius of cone for cone search in arcmin. 
		pmra (float): Central RA proper motion around which to allow the tolerance pmthresh.
		pmd (float): Central Dec proper motion around which to allow the tolerance pmthresh.
		pmthresh (float): Tolerance for proper motions included in CMD.

	Returns:
		Catalog of Gaia stars.
	"""

	cs = Gaia.cone_search_async(objloc(obj), radius=u.Quantity(aper, u.arcmin))
	tab = cs.get_results()
	# keep only values that have photometry
	tab = tab[np.isfinite(tab['phot_bp_mean_mag']) & np.isfinite(tab['phot_rp_mean_mag']) & np.isfinite(tab['phot_g_mean_mag']) ]

	## will add parallax selection in the future?

	if pmra:
		tab = tab[abs(tab['pmra'] - pmra) <= pmthresh]
	if pmd:
		tab = tab[abs(tab['pmdec'] - pmd) <= pmthresh]

	return tab


def isochrone(logage, feh, dist = 10., blue = 'bp', red = 'rp', mag = 'rp', isos = 'mist'):
	"""
	Return MIST or Parsec synthetic photometry for Gaia EDR3.

	Parameters:
		logage (float): Log age/yrs of isochrone.
		feh (float): [Fe/H] of isochrone.
		dist (float): Distance in parsecs.
		blue (str): 'bp' or 'g'; blue band for color
		red (str): 'g' or 'rp'; red band for color
		mag (str): 'bp', 'g', or 'rp', band to use for magnitude in CMD.
		isos (str): 'mist' or 'parsec'; model isochrones to use.

	Returns:
		color, magnitude
	"""
	url_base = 'https://raw.githubusercontent.com/avapolzin/goodenough_gaia_cmds/refs/heads/main/isos/%s_gaia_edr3.txt'%isos.lower()
	if isos.lower() in ['mist', 'parsec']:
		iso = pd.read_csv(url_base, sep = ',', header = 0)

	ages = np.sort(np.unique(iso['logage'].values))
	mets = np.sort(np.unique(iso['feh'].values))

	## not interpolating, so grabbing isochrones with *nearest* properties
	near_age = ages[np.argmin(abs(ages - logage))]
	near_met = mets[np.argmin(abs(mets - feh))]

	near_iso = iso.loc[(iso['logage'] == near_age) & (iso['feh'] == near_met)]

	color = near_iso[blue.lower()] - near_iso[red.lower()]
	magn = near_iso[mag.lower()] + 5*np.log10(dist/10) #adjust to apparent magnitude if distance specified

	print('Closest match in %s: log age/yr = %.2f, [Fe/H] = %.2f'%(isos.upper(), near_age, near_met))

	return color, magn


def plot(obj, aper, pmra = None, pmd = None, pmthresh = 0.5, isos = None, logage = None, 
			feh = None, dist = 10., blue = 'bp', red = 'rp', mag = 'g', cfield = None, 
			cmap = 'viridis', cmdcol = 'k', cmdalpha = 1., isocol = 'mediumvioletred', 
			absmag = False, showspatial = False):
	"""
	Plot CMD of stars within cone of specified obj. If isos, will overplot isochrones with stated parameters.

	Parameters:
		obj (str): Name or coordinates for object of interest. If coordinates, should be in
			HH:MM:SS DD:MM:SS or degree formats. Names must be resolvable in SIMBAD.
		aper (float): Radius of cone for cone search in arcmin. 
		pmra (float): Central RA proper motion around which to allow the tolerance pmthresh.
		pmd (float): Central Dec proper motion around which to allow the tolerance pmthresh.
		pmthresh (float): Tolerance for proper motions included in CMD.
		isos (str): None, 'mist', or 'parsec'; model isochrones to use. If None, will not plot isochrone.
		logage (float): Log age/yrs of isochrone.
		feh (float): [Fe/H] of isochrone.
		dist (float): Distance in parsecs.
		blue (str): 'bp' or 'g'; blue band for color
		red (str): 'g' or 'rp'; red band for color
		mag (str): 'bp', 'g', or 'rp', band to use for magnitude in CMD.
		cfield (str): Color points by one of Gaia table column names: 'solution_id','designation','source_id',
				'random_index','ref_epoch','ra','ra_error','dec','dec_error','parallax','parallax_error',
				'parallax_over_error','pm','pmra','pmra_error','pmdec','pmdec_error','ra_dec_corr',
				'ra_parallax_corr','ra_pmra_corr','ra_pmdec_corr','dec_parallax_corr','dec_pmra_corr',
				'dec_pmdec_corr','parallax_pmra_corr','parallax_pmdec_corr','pmra_pmdec_corr',
				'astrometric_n_obs_al','astrometric_n_obs_ac','astrometric_n_good_obs_al',
				'astrometric_n_bad_obs_al','astrometric_gof_al','astrometric_chi2_al',
				'astrometric_excess_noise','astrometric_excess_noise_sig','astrometric_params_solved',
				'astrometric_primary_flag','nu_eff_used_in_astrometry','pseudocolour','pseudocolour_error',
				'ra_pseudocolour_corr','dec_pseudocolour_corr','parallax_pseudocolour_corr',
				'pmra_pseudocolour_corr','pmdec_pseudocolour_corr','astrometric_matched_transits',
				'visibility_periods_used','astrometric_sigma5d_max','matched_transits','new_matched_transits',
				'matched_transits_removed','ipd_gof_harmonic_amplitude','ipd_gof_harmonic_phase',
				'ipd_frac_multi_peak','ipd_frac_odd_win','ruwe','scan_direction_strength_k1',
				'scan_direction_strength_k2','scan_direction_strength_k3','scan_direction_strength_k4',
				'scan_direction_mean_k1','scan_direction_mean_k2','scan_direction_mean_k3',
				'scan_direction_mean_k4','duplicated_source','phot_g_n_obs','phot_g_mean_flux',
				'phot_g_mean_flux_error','phot_g_mean_flux_over_error','phot_g_mean_mag','phot_bp_n_obs',
				'phot_bp_mean_flux','phot_bp_mean_flux_error','phot_bp_mean_flux_over_error','phot_bp_mean_mag',
				'phot_rp_n_obs','phot_rp_mean_flux','phot_rp_mean_flux_error','phot_rp_mean_flux_over_error',
				'phot_rp_mean_mag','phot_bp_rp_excess_factor','phot_bp_n_contaminated_transits',
				'phot_bp_n_blended_transits','phot_rp_n_contaminated_transits','phot_rp_n_blended_transits',
				'phot_proc_mode','bp_rp','bp_g','g_rp','radial_velocity','radial_velocity_error','rv_method_used',
				'rv_nb_transits','rv_nb_deblended_transits','rv_visibility_periods_used','rv_expected_sig_to_noise',
				'rv_renormalised_gof','rv_chisq_pvalue','rv_time_duration','rv_amplitude_robust','rv_template_teff',
				'rv_template_logg','rv_template_fe_h','rv_atm_param_origin','vbroad','vbroad_error',
				'vbroad_nb_transits','grvs_mag','grvs_mag_error','grvs_mag_nb_transits','rvs_spec_sig_to_noise',
				'phot_variable_flag','l','b','ecl_lon','ecl_lat','in_qso_candidates','in_galaxy_candidates',
				'non_single_star','has_xp_continuous','has_xp_sampled','has_rvs','has_epoch_photometry','has_epoch_rv',
				'has_mcmc_gspphot','has_mcmc_msc','in_andromeda_survey','classprob_dsc_combmod_quasar',
				'classprob_dsc_combmod_galaxy','classprob_dsc_combmod_star','teff_gspphot','teff_gspphot_lower',
				'teff_gspphot_upper','logg_gspphot','logg_gspphot_lower','logg_gspphot_upper','mh_gspphot',
				'mh_gspphot_lower','mh_gspphot_upper','distance_gspphot','distance_gspphot_lower',
				'distance_gspphot_upper','azero_gspphot','azero_gspphot_lower','azero_gspphot_upper',
				'ag_gspphot','ag_gspphot_lower','ag_gspphot_upper','ebpminrp_gspphot','ebpminrp_gspphot_lower',
				'ebpminrp_gspphot_upper','libname_gspphot','dist'
		cmap (str): Colormap to use with cfield.
		cmdcol (str): Color for data points in CMD.
		cmdalpha (float): Opacity of points in CMD.
		isocol (str): Color for isochrone if shown.
		absmag (bool): If True, uses parallax distance to put CMD in absolute magnitude.
		showspatial (bool): If showspatial, creates subplot that shows RA/Dec distribution of Gaia sources.

	Returns:
		Plot showing CMD for stars within cone of specified obj, and, if isos, will overplot isochrone.
	"""

	dat = select(obj, aper, pmra, pmd, pmthresh)
	cind = dat['%s_%s'%(blue, red)]
	mind = dat['phot_%s_mean_mag'%mag]

	maglabel = mag.upper()
	dcorr = 0
	if absmag:
		dcorr = 1e-6/abs(dat['parallax']) #mas
		maglabel = 'absolute %s'%mag.upper()
		mind -= 5*np.log10(dcorr/10)


	if not showspatial:
		if not cfield:
			fig = plt.figure(figsize = (4, 4), dpi = 150)
			plt.scatter(cind, mind , color = cmdcol, alpha = cmdalpha)
		if cfield:
			fig = plt.figure(figsize = (5, 4), dpi = 150)
			plt.scatter(cind, mind, c = dat[cfield], cmap = cmap, alpha = cmdalpha)
			plt.colorbar(label = cfield)

		if isos:
			if None in [logage, feh]:
				raise ValueError('If isos, logage and feh must be provided.')

			iso = isochrone(logage, feh, dist, blue, red, mag, isos)
			plt.plot(iso[0], iso[1], color = isocol, lw = 2)

		plt.title(obj)
		plt.gca().invert_yaxis()
		plt.ylabel(maglabel)
		plt.xlabel('%s - %s'%(blue.upper(), red.upper()))
		plt.show()

	if showspatial:
		if not cfield:
			fig, ax = plt.subplots(1, 2, figsize = (8.5, 4), dpi = 150)
			ax[0].scatter(cind, mind , color = cmdcol, alpha = cmdalpha)
			ax[1].scatter(dat['ra'], dat['dec'], color = cmdcol)
		if cfield:
			fig, ax = plt.subplots(1, 2, figsize = (10, 4), dpi = 150)
			cbar = ax[0].scatter(cind, mind, c = dat[cfield], cmap = cmap, alpha = cmdalpha)
			ax[1].scatter(dat['ra'], dat['dec'], c = dat[cfield], cmap = cmap)
			plt.colorbar(cbar, ax = ax, label = cfield, pad = 0)

		if isos:
			if None in [logage, feh]:
				raise ValueError('If isos, logage and feh must be provided.')

			iso = isochrone(logage, feh, dist, blue, red, mag, isos)
			ax[0].plot(iso[0], iso[1], color = isocol, lw = 2)

		plt.suptitle(obj)
		ax[0].invert_yaxis()
		ax[0].set_ylabel(maglabel)
		ax[0].set_xlabel('%s - %s'%(blue.upper(), red.upper()))

		ax[1].set_ylabel('Dec')
		ax[1].set_xlabel('RA')









