import numpy as np
import xarray as xr
from typing import Sequence,Literal

from ...core.coords import destagger_array
from ...core.vertical import vertical_interp

def _new_croco_coords(da: xr.Dataset, ds_meta: dict[str, list], lats: list | xr.DataArray, lons: list | xr.DataArray,
    destag: bool = True, lats_v: list | xr.DataArray = None, lons_u: list | xr.DataArray = None) -> xr.Dataset:
    """
    Applies coordinate standardization and destaggering to CROCO output data.

    Parameters
    ----------
    da : xr.Dataset
        CROCO output dataset.

    ds_meta : dict[str, list]
        Metadata dictionary from `get_metadata_vars`.

    lats : list | xr.DataArray
        Latitude array along eta_rho.

    lons : list | xr.DataArray
        Longitude array along xi_rho.

    destag : bool, default=True
        Whether to apply destaggering to staggered dimensions.

    lats_v : list | xr.DataArray, optional
        Latitude for eta_v (only used if `destag=False`).

    lons_u : list | xr.DataArray, optional
        Longitude for xi_u (only used if `destag=False`).

    Returns
    -------
    xr.Dataset
        Standardized and optionally destaggered CROCO dataset with renamed coordinates.
    """
    list_X = [key for key, list_values in ds_meta.items() if 'xi_u' in list_values[0]]
    list_Y = [key for key, list_values in ds_meta.items() if 'eta_v' in list_values[0]]
    list_Z = list(set([key for key, list_values in ds_meta.items() if 's_w' in list_values[0]])-set(['Cs_w','sc_w']))

    if destag:
        for var in da:
            if var in list_Z:
                da[var] = destagger_array(da[var],axis='s_w',pad=False).rename({'s_w':'s_rho'})
            if var in list_X:
                da[var] = destagger_array(da[var],axis = 'xi_u',pad=True).rename({'xi_u':'xi_rho'})
            if var in list_Y:
                da[var] = destagger_array(da[var],axis='eta_v',pad=True).rename({'eta_v':'eta_rho'})
    else:
        for var in da:
            if var in list_X and lons_u is not None:
                da[var] = da[var].assign_coords(xi_u=('xi_u',lons_u)).rename({'xi_u':'lons_u'})
            elif var in list_Y and lats_v is not None:
                da[var] = da[var].assign_coords(eta_v=('eta_v',lats_v)).rename({'eta_v':'lats_v'})

    da = da.assign_coords(
        xi_rho=('xi_rho',lons),
        eta_rho=('eta_rho',lats),
    )

    drop_coords = ["xi_u", "eta_v", "lat_rho", "lon_rho",'lon_u','lon_v','lat_u','lat_v']
    da = da.drop_vars([c for c in drop_coords if c in da.variables], errors="ignore")
    da = da.rename({'eta_rho':'lat','xi_rho':'lon','s_rho':'levels'})
    da['lat'].attrs = {"units": 'degrees_north', 'axis': 'Y','long_name':'Latitude','standard_name':'latitude'}
    da['lon'].attrs = {"units": 'degrees_east', 'axis': 'X','long_name':'Longitude','standard_name':'longitude'}

    for var in da.data_vars:
        coords = da[var].coords
        if all(c in coords for c in ["lat", "lon"]) and ("time" in coords or "time" in da.dims):
            if "time" in da[var].dims:
                da[var].encoding["coordinates"] = "time lat lon"
            else:
                da[var].encoding["coordinates"] = "lat lon"

    return da

def croco_depths(
    ds: xr.Dataset,
    *,
    which: Literal["rho", "w"] = "rho",
    levels_dim: str = "levels",
    wlevels_dim: str = "s_w",
    lat_dim: str = "lat",
    lon_dim: str = "lon",
    h_name: str = "h",
    zeta_name: str = "zeta",
    hc_name: str = "hc"
) -> xr.DataArray:
    """
    Compute physical depths (z, in meters) at rho or w points for CROCO/ROMS grids.

    This function is compatible with datasets produced by `read_croco` and
    computes the vertical coordinate transformation according to the model
    parameters, supporting both **Vtransform = 1** and **Vtransform = 2**.
    It does not create artificial dimensions and follows the original structure
    of the CROCO vertical grid.

    Parameters
    ----------
    ds : xr.Dataset
        CROCO dataset already standardized (as returned by `read_croco`).
    which : {'rho', 'w'}, default 'rho'
        Defines the grid points where depths are computed:
        - `'rho'` → centers of vertical layers (used for T, S, U, V)
        - `'w'`   → interfaces between layers (used for vertical velocity)
    levels_dim : str, optional
        Name of the vertical dimension for rho-points (default: "levels").
    wlevels_dim : str, optional
        Name of the vertical dimension for w-points (default: "s_w").
    lat_dim, lon_dim : str, optional
        Names of the horizontal dimensions (default: "lat", "lon").
    h_name, zeta_name, hc_name : str, optional
        Names of the bathymetry (`h`), free-surface elevation (`zeta`),
        and critical depth (`hc`) variables.

    Returns
    -------
    xr.DataArray
        Physical depth (in meters) at either rho-points or w-points:
        - For `'rho'` → dimensions (time, levels, lat, lon)
        - For `'w'`   → dimensions (time, s_w, lat, lon)

    """
    if which == "rho":

        if levels_dim not in ds.coords:
            raise KeyError(f"Coordenada vertical '{levels_dim}' no encontrada en coords.")
        s = ds.coords[levels_dim]                     

        C_candidates = ["Cs_rho", "Cs_r"]           
        C_name = next((v for v in C_candidates if v in ds.variables), None)
        if C_name is None:
            raise KeyError("No se encontró 'Cs_rho' (ni 'Cs_r').")
        C = ds[C_name]                               

        s_dim = levels_dim

    else:  
        if wlevels_dim not in ds.coords:
            raise KeyError(f"Coordenada vertical '{wlevels_dim}' no encontrada en coords.")
        s = ds.coords[wlevels_dim]                   

        C_name = "Cs_w"
        if C_name not in ds:
            raise KeyError("No se encontró 'Cs_w'.")
        C = ds[C_name]                              

        s_dim = wlevels_dim

    if h_name not in ds or zeta_name not in ds or hc_name not in ds:
        raise KeyError("Faltan 'h', 'zeta' o 'hc' en el dataset.")

    h = ds[h_name]                                   
    zeta = ds[zeta_name]                             
    hc = ds[hc_name]                                 

    if 'Vtransform' in ds:
        Vt = int(np.asarray(ds['Vtransform']).item())
    else:
        Vt = int(ds.attrs.get("Vtransform", ds.attrs.get("vtransform", 2)))


    if Vt == 1:
        S = hc * s + (h - hc) * C                    
        z = S + zeta * (1.0 + S / h)                
    elif Vt == 2:
        S = (hc * s + h * C) / (hc + h)             
        z = zeta + (zeta + h) * S                   
    else:
        raise ValueError(f"Vtransform={Vt} no soportado (esperado 1 o 2).")

    dims_out = [d for d in ("time", s_dim, lat_dim, lon_dim) if d in z.dims]
    z = z.transpose(*dims_out)

    z.name = f"z_{which}"
    z.attrs.update({
        "units": "m",
        "long_name": f"Depth at {which}-points (Vtransform={Vt})",
    })
    return z


def crocointerp_sigma_to_z(
    ds: xr.Dataset,
    var_names: Sequence[str],
    *,
    which_z: Literal["rho", "w"] = "rho",
    z_levels: Sequence[float] | None = None,
    z_units: Literal["m", "km"] = "m",
    sigma_dim: str | None = None,      
    new_dim: str = "z",
    mask_outside: bool = True,
    nan_opt:str = 'both',
) -> xr.Dataset:
    """
    Interpolate CROCO variables from sigma levels to fixed z levels (meters).

    Parameters
    ----------
    ds : xr.Dataset
        CROCO Dataset con h, zeta, hc, s_{rho|w}, Cs_{r|w}.
    var_names : sequence of str
        Variables a interpolar (deben contener la dimensión sigma).
    which_z : {'rho','w'}, default 'rho'
        Profundidades de referencia para la interpolación (z_r o z_w).
    z_levels : sequence of float or None
        Niveles objetivo en z. Si None, usa [0, -10, -20, -30, -50, -75, -100,
        -150, -200, -300, -500, -1000].
    z_units : {'m','km'}, default 'm'
        Unidades de z_levels.
    sigma_dim : str or None
        Nombre de la dimensión sigma; si None se infiere ('levels' o 's_w').
    new_dim : str, default 'z'
        Nombre de la nueva dimensión.
    mask_outside : bool, default True
        Enmascara con NaN los puntos fuera del rango vertical local.
    nan_opt : {"both", "left", "right", "none"}, default "both"
        - "both": no extrapolation (NaN on both sides)
        - "left": NaN on the left, extrapolate on the right
        - "right": extrapolate on the left, NaN on the right
        - "none": extrapolate on both sides

    Returns
    -------
    xr.Dataset
        Dataset con variables interpoladas en el eje `new_dim` (z).
    """
    if sigma_dim is None:
        sigma_dim = "levels" if which_z == "rho" else "s_w"

    if z_levels is None:
        z_levels = [0, -10, -20, -30, -50, -75, -100, -150, -200, -300, -500, -1000]
    z_levels = np.asarray(z_levels, dtype=float)
    if z_units == "km":
        z_levels = z_levels * 1000.0

    z = croco_depths(ds, which=which_z)

    outs = []
    for v in var_names:
        if v not in ds:
            raise KeyError(f"Variable '{v}' not found in dataset.")
        da = ds[v]
        if sigma_dim not in da.dims:
            raise ValueError(f"Variable '{v}' is missing vertical dim '{sigma_dim}'.")

        dai = vertical_interp(
            da=da,
            coord=z,
            new_levels=z_levels,
            dim=sigma_dim,
            new_dim=new_dim,
            keep_attrs=True,
            nan_opt=nan_opt,
        )

        if mask_outside:
            zmin = z.min(dim=sigma_dim)
            zmax = z.max(dim=sigma_dim)
            low = xr.apply_ufunc(np.minimum, zmin, zmax)
            high = xr.apply_ufunc(np.maximum, zmin, zmax)
            valid = (dai[new_dim] >= low) & (dai[new_dim] <= high)
            dai = dai.where(valid)

        dai.name = v
        dai.attrs["interp_coord"] = "z"
        dai.attrs["levels_units"] = "m"
        dai.attrs["long_name"] = da.attrs.get("long_name", v) + " (interpolated to z)"

        outs.append(dai.to_dataset())

    ds_out = xr.merge(outs).assign_coords({new_dim: z_levels})

    for c in ("lat", "lon", "time"):
        if c in ds:
            ds_out = ds_out.assign_coords({c: ds[c]})
    if "time" in ds_out:
        ds_out.encoding["unlimited_dims"] = ("time",)

    if "lat" in ds_out:
        ds_out["lat"].attrs = {
            "units": "degrees_north", "axis": "Y",
            "long_name": "Latitude", "standard_name": "latitude",
        }
    if "lon" in ds_out:
        ds_out["lon"].attrs = {
            "units": "degrees_east", "axis": "X",
            "long_name": "Longitude", "standard_name": "longitude",
        }

    return ds_out