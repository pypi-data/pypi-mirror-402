from calcephpy import CalcephBin, NaifId, Constants
import numpy as np
import os


constants_kms = Constants.UNIT_KM | Constants.UNIT_SEC | Constants.USE_NAIFID
constants_auday = Constants.UNIT_AU | Constants.UNIT_DAY | Constants.USE_NAIFID


# Open Ephemeris
# eph:DE440
eph = None


# eph2:lte440
lte440bsp_path = os.path.join(os.path.dirname(__file__), 'lte440.bsp')
lte440tpc_path = os.path.join(os.path.dirname(__file__), 'lte440.tpc')
eph2 = CalcephBin.open([lte440bsp_path, lte440tpc_path])


# Call the Earth Time Ephemeris from the path entered by the user
def init_E(path):
    # change global eph
    global eph, AU, c, GME, GMM, GMS, GM_mer, GM_ven, GM_mar, GM_jup, GM_sat, GM_ura, GM_nep, GM_plu

    eph = CalcephBin.open(path)

    # Physical Constants (Read from DE440)
    # Astronomical unit, km
    AU = 0.149597870700000000e+09

    # light speed, km/s
    c = 0.299792458000000000e+06

    # Gravitational Constants of Solar System Objects
    # GM of Earth, km^3/s^2
    GME = 0.888769244670710310e-09 * AU**3 / 86400**2

    # GM of Moon, km^3/s^2
    GMM = 0.109318946240243499e-10 * AU**3 / 86400**2

    # GM of Sun, km^3/s^2
    GMS = 0.295912208284119561e-03 * AU**3 / 86400**2

    # GM of Mercury, km^3/s^2
    GM_mer = 0.491250019488931818e-10 * AU**3 / 86400**2

    # GM of Venus, km^3/s^2
    GM_ven = 0.724345233264411869e-09 * AU**3 / 86400**2

    # GM of Mars, km^3/s^2
    GM_mar = 0.954954882972581189e-10 * AU**3 / 86400**2

    # GM of Jupiter, km^3/s^2
    GM_jup = 0.282534582522579175e-06 * AU**3 / 86400**2

    # GM of Saturn, km^3/s^2
    GM_sat = 0.845970599337629027e-07 * AU**3 / 86400**2

    # GM of Uranus, km^3/s^2
    GM_ura = 0.129202656496823994e-07 * AU**3 / 86400**2

    # GM of Neptune, km^3/s^2
    GM_nep = 0.152435734788519386e-07 * AU**3 / 86400**2

    # GM of Pluto, km^3/s^2
    GM_plu = 0.217509646489335811e-11 * AU**3 / 86400**2


# Call the Lunar Time Ephemeris from the path entered by the user
def init_M(path):
    # change global eph2
    global eph2
    eph2 = CalcephBin.open(path)


# Defined Constants
# Scale factor of TT and TCG
L_G = 6.969290134 * 10**(-10)

# Scale factor of TDB and TCB
L_B = 1.550519768 * 10**(-8)

# Number of seconds of a Julian Day
day = 86400


##############################################################################


# Function for calculating certain physical quantities


# Accelaration of Earth
def comp_aE(jd1, jd2):
    delta_t = 10 / day
    pv_earth_1 = eph.compute_unit(jd1, jd2 - delta_t,
                                  NaifId.EARTH,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    v_E1 = np.array([pv_earth_1[3], pv_earth_1[4], pv_earth_1[5]])

    pv_earth_2 = eph.compute_unit(jd1, jd2 + delta_t,
                                  NaifId.EARTH,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    v_E2 = np.array([pv_earth_2[3], pv_earth_2[4], pv_earth_2[5]])
    a_E = (v_E2 - v_E1) / (2 * delta_t * day)
    return a_E


# Accelaration of Moon
def comp_aM(jd1, jd2):
    delta_t = 10 / day
    pv_moon_1 = eph.compute_unit(jd1, jd2 - delta_t,
                                 NaifId.MOON,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    v_M1 = np.array([pv_moon_1[3], pv_moon_1[4], pv_moon_1[5]])

    pv_moon_2 = eph.compute_unit(jd1, jd2 + delta_t,
                                 NaifId.MOON,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    v_M2 = np.array([pv_moon_2[3], pv_moon_2[4], pv_moon_2[5]])
    a_M = (v_M2 - v_M1) / (2 * delta_t * day)
    return a_M


# Newtonian potential of Earth (including the Sun, Moon, Planets and Pluto )
def comp_w0E(jd1, jd2):
    # position of Earth
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])

    # position of Moon
    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])

    # position of Sun
    pv_sun = eph.compute_unit(jd1, jd2,
                              NaifId.SUN,
                              NaifId.SOLAR_SYSTEM_BARYCENTER,
                              constants_kms)
    xs_sun = np.array([pv_sun[0], pv_sun[1], pv_sun[2]])

    # position of Mercury
    pv_mercury = eph.compute_unit(jd1, jd2,
                                  NaifId.MERCURY_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_mer = np.array([pv_mercury[0], pv_mercury[1], pv_mercury[2]])

    # position of Venus
    pv_venus = eph.compute_unit(jd1, jd2,
                                NaifId.VENUS_BARYCENTER,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_ven = np.array([pv_venus[0], pv_venus[1], pv_venus[2]])

    # position of Mars
    pv_mars = eph.compute_unit(jd1, jd2,
                               NaifId.MARS_BARYCENTER,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_mar = np.array([pv_mars[0], pv_mars[1], pv_mars[2]])

    # position of Jupiter
    pv_jupiter = eph.compute_unit(jd1, jd2,
                                  NaifId.JUPITER_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_jup = np.array([pv_jupiter[0], pv_jupiter[1], pv_jupiter[2]])

    # position of Saturn
    pv_saturn = eph.compute_unit(jd1, jd2,
                                 NaifId.SATURN_BARYCENTER,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    xs_sat = np.array([pv_saturn[0], pv_saturn[1], pv_saturn[2]])

    # position of Uranus
    pv_uranus = eph.compute_unit(jd1, jd2,
                                 NaifId.URANUS_BARYCENTER,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    xs_ura = np.array([pv_uranus[0], pv_uranus[1], pv_uranus[2]])

    # position of Neptune
    pv_neptune = eph.compute_unit(jd1, jd2,
                                  NaifId.NEPTUNE_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_nep = np.array([pv_neptune[0], pv_neptune[1], pv_neptune[2]])

    # position of Pluto
    pv_pluto = eph.compute_unit(jd1, jd2,
                                NaifId.PLUTO_BARYCENTER,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_plu = np.array([pv_pluto[0], pv_pluto[1], pv_pluto[2]])

    w_0E = GMS / np.linalg.norm(xs_E - xs_sun) + GMM / np.linalg.norm(xs_E - xs_M) \
        + GM_mer / np.linalg.norm(xs_E - xs_mer) \
        + GM_ven / np.linalg.norm(xs_E - xs_ven) \
        + GM_mar / np.linalg.norm(xs_E - xs_mar) \
        + GM_jup / np.linalg.norm(xs_E - xs_jup) \
        + GM_sat / np.linalg.norm(xs_E - xs_sat) \
        + GM_ura / np.linalg.norm(xs_E - xs_ura) \
        + GM_nep / np.linalg.norm(xs_E - xs_nep) \
        + GM_plu / np.linalg.norm(xs_E - xs_plu)
    return w_0E


# Newtonian potential of Monn (including the Sun, Earth, Planets and Pluto )
def comp_w0M(jd1, jd2):
    # position of Earth
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])

    # position of Moon
    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])

    # position of Sun
    pv_sun = eph.compute_unit(jd1, jd2,
                              NaifId.SUN,
                              NaifId.SOLAR_SYSTEM_BARYCENTER,
                              constants_kms)
    xs_sun = np.array([pv_sun[0], pv_sun[1], pv_sun[2]])

    # position of Mercury
    pv_mercury = eph.compute_unit(jd1, jd2,
                                  NaifId.MERCURY_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_mer = np.array([pv_mercury[0], pv_mercury[1], pv_mercury[2]])

    # position of Venus
    pv_venus = eph.compute_unit(jd1, jd2,
                                NaifId.VENUS_BARYCENTER,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_ven = np.array([pv_venus[0], pv_venus[1], pv_venus[2]])

    # position of Mars
    pv_mars = eph.compute_unit(jd1, jd2,
                               NaifId.MARS_BARYCENTER,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_mar = np.array([pv_mars[0], pv_mars[1], pv_mars[2]])

    # position of Jupiter
    pv_jupiter = eph.compute_unit(jd1, jd2,
                                  NaifId.JUPITER_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_jup = np.array([pv_jupiter[0], pv_jupiter[1], pv_jupiter[2]])

    # position of Saturn
    pv_saturn = eph.compute_unit(jd1, jd2,
                                 NaifId.SATURN_BARYCENTER,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    xs_sat = np.array([pv_saturn[0], pv_saturn[1], pv_saturn[2]])

    # position of Uranus
    pv_uranus = eph.compute_unit(jd1, jd2,
                                 NaifId.URANUS_BARYCENTER,
                                 NaifId.SOLAR_SYSTEM_BARYCENTER,
                                 constants_kms)
    xs_ura = np.array([pv_uranus[0], pv_uranus[1], pv_uranus[2]])

    # position of Neptune
    pv_neptune = eph.compute_unit(jd1, jd2,
                                  NaifId.NEPTUNE_BARYCENTER,
                                  NaifId.SOLAR_SYSTEM_BARYCENTER,
                                  constants_kms)
    xs_nep = np.array([pv_neptune[0], pv_neptune[1], pv_neptune[2]])

    # position of Pluto
    pv_pluto = eph.compute_unit(jd1, jd2,
                                NaifId.PLUTO_BARYCENTER,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_plu = np.array([pv_pluto[0], pv_pluto[1], pv_pluto[2]])

    w_0M = GMS / np.linalg.norm(xs_M - xs_sun) + GME / np.linalg.norm(xs_M - xs_E) \
        + GM_mer / np.linalg.norm(xs_M - xs_mer) \
        + GM_ven / np.linalg.norm(xs_M - xs_ven) \
        + GM_mar / np.linalg.norm(xs_M - xs_mar) \
        + GM_jup / np.linalg.norm(xs_M - xs_jup) \
        + GM_sat / np.linalg.norm(xs_M - xs_sat) \
        + GM_ura / np.linalg.norm(xs_M - xs_ura) \
        + GM_nep / np.linalg.norm(xs_M - xs_nep) \
        + GM_plu / np.linalg.norm(xs_M - xs_plu)
    return w_0M


##############################################################################


# TDB-TT

# Calculation Notes:
# The space-time transformation from (TDB, x*) to (TT, X*) can be calculated
# using the function TDB2TT.
# Note that although the function name only includes time scales, it actually
# also incorporates spatial coordinate transformation.
# This function divides the differences between time scales into position-independent
# terms and position-dependent terms, which can be calculated by the functions
# FDTE and FPD respectively.
# The differences between spatial coordinates can be obtained using the function FPDX.


# Position-independent term in TDB to TT (s)
def FDTE(jd1, jd2):
    DTE = eph.compute_unit(jd1, jd2, NaifId.TIME_TTMTDB, NaifId.TIME_CENTER, constants_kms)
    return DTE[0]


# Position-dependent term in TDB to TT (s)
def FPD(jd1, jd2, xs):
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])   # position of Earth
    v_E = np.array([pv_earth[3], pv_earth[4], pv_earth[5]])   # velocity of Earth

    w_0E = comp_w0E(jd1, jd2)   # Newtonian potential

    rs_E = xs - xs_E   # position relative to Earth

    # Calculate the position-dependent term PD in TT-TDB
    PD = (1 - L_G) / (1 - L_B) * (-1 / c**2 * np.dot(v_E, rs_E)
                                  - 1 / c**4 * (3 * w_0E + np.dot(v_E, v_E) / 2) * np.dot(v_E, rs_E))

    return PD


# space transformation function in TDB to TT (km)
def FPDX(jd1, jd2, xs):
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])   # position of Earth
    v_E = np.array([pv_earth[3], pv_earth[4], pv_earth[5]])   # velocity of Earth
    as_E = comp_aE(jd1, jd2)                                # acceleration of Earth

    w_0E = comp_w0E(jd1, jd2)   # Newtonian potential

    rs_E = xs - xs_E   # position relative to Earth

    # Calculate the X* - x*
    PDX = (L_B - L_G) / (1 - L_B) * rs_E + (1 - L_G) / (1 - L_B) * 1 / c**2 * (
        1/2 * np.dot(v_E, rs_E) * v_E + w_0E * rs_E
        + np.dot(as_E, rs_E) * rs_E - 1/2 * as_E * np.dot(rs_E, rs_E))

    return PDX


# (TDB, xs) to (TT, Xs)

def TDB2TT(jd1, jd2, xs):
    # time transformation
    dt = FDTE(jd1, jd2) + FPD(jd1, jd2, xs)
    TT1 = jd1 + int(dt / day)
    TT2 = jd2 + dt / day - int(dt / day)

    # space transformation
    dx = FPDX(jd1, jd2, xs)
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])
    Xs = xs - xs_E + dx
    return TT1, TT2, Xs


# TT-TDB


# Calculation Notes:
# The transformation from (TT, X*) to (TDB, x*) adopts an iterative algorithm.
# The iterative error precisions for time and space transformations are both
# optional parameters, with default values of 1 nanosecond and 1 millimeter, respectively.


def TT2TDB(jd1, jd2, Xs, Delta_t=10**(-9), Delta_x=10**(-6)):   # Delta_t: time error (s), Delta_x: positioin error (km)
    def tt2tdb(jdt1, jdt2, xsx):
        pv_earth = eph.compute_unit(jdt1, jdt2,
                                    NaifId.EARTH,
                                    NaifId.SOLAR_SYSTEM_BARYCENTER,
                                    constants_kms)
        xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])

        # time transformation
        dt = FDTE(jdt1, jdt2) + FPD(jdt1, jdt2, xsx)
        TDBn1 = jd1 - int(dt / day)
        TDBn2 = jd2 - dt / day + int(dt / day)

        # space transformation
        dx = FPDX(jdt1, jdt2, xsx)
        xsn = Xs + xs_E - dx

        return TDBn1, TDBn2, xsn

    dtz = 1000   # Initial settings, facilitating the start of the cycle
    dxz = 1

    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])

    TDB1_0 = jd1
    TDB2_0 = jd2
    xs_0 = Xs + xs_E

    while abs(dtz) > Delta_t or abs(dxz) > Delta_x:
        TDB1_1, TDB2_1, xs_1 = TDB1_0, TDB2_0, xs_0
        TDB1_0, TDB2_0, xs_0 = tt2tdb(TDB1_1, TDB2_1, xs_1)
        dtz = ((TDB1_0 - TDB1_1) + (TDB2_0 - TDB2_1)) * day
        dxz = np.linalg.norm(xs_0 - xs_1)

    return TDB1_0, TDB2_0, xs_0


##############################################################################


##############################################################################
# TDB - TCL


# Calculation Notes:
# The space-time transformation from (TDB, x*) to (TCL, Y) can be calculated
# using the function TDB2TCL.
# Note that although the function name only includes time scales, it actually
# also incorporates spatial coordinate transformation.
# This function divides the differences between time scales into position-independent
# terms and position-dependent terms, which can be calculated by the functions
# FLDTE and FLPD respectively.
# The differences between spatial coordinates can be obtained using the function FPDY.


# Position-independent terms LTE (s)

def FLDTE(jd1, jd2):
    TDB0 = -65.5e-6         # TDB0 in seconds
    T0_JD1 = 2443144.5
    T0_JD2 = 0.0003725 + TDB0 / 86400

    # Naif ID for the dummy center body
    center = NaifId.TIME_CENTER
    # Naif ID for TCL-TCB
    target = eph2.getidbyname('TIME_TCLMTDB', Constants.USE_NAIFID)

    # Function `compute_unit` returns [X, Y, Z, VX, VY, VZ]
    pv = eph2.compute_unit(jd1, jd2, target, center, constants_kms)
    # LTE data is in the X coordinate
    lte_periodic = pv[0]

    # Read drift rate from the PCK kernel, name is "BODY<target>_RATE"
    drift = eph2.getconstant(f'BODY{target}_RATE')

    # Calculate the total TCL-TCB
    dTDB = ((jd1 - T0_JD1) + (jd2 - T0_JD2)) * 86400
    tcl_tdb = lte_periodic + drift * dTDB

    return tcl_tdb


# Position-dependent term in TDB to TCL (s)
def FLPD(jd1, jd2, xs):
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])   # position of Earth
    v_E = np.array([pv_earth[3], pv_earth[4], pv_earth[5]])   # velocity of Earth

    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])   # position of Moon
    v_M = np.array([pv_moon[3], pv_moon[4], pv_moon[5]])   # velocity of Moon

    w_0M = comp_w0M(jd1, jd2)   # Newtonian potential

    rs_M = xs - xs_M   # position relative to Moon

    # Calculate the position-dependent term LPD in TCL-TDB
    LPD = 1 / (1 - L_B) * (-1 / c**2 * np.dot(v_M, rs_M)
                           - 1 / c**4 * (3 * w_0M + np.dot(v_M, v_M) / 2) * np.dot(v_M, rs_M))
    return LPD


# space transformation function in TDB to TCL (km)
def FPDY(jd1, jd2, xs):
    pv_earth = eph.compute_unit(jd1, jd2,
                                NaifId.EARTH,
                                NaifId.SOLAR_SYSTEM_BARYCENTER,
                                constants_kms)
    xs_E = np.array([pv_earth[0], pv_earth[1], pv_earth[2]])   # position of Earth
    v_E = np.array([pv_earth[3], pv_earth[4], pv_earth[5]])   # velocity of Earth
    as_E = comp_aE(jd1, jd2)

    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])   # position of Moon
    v_M = np.array([pv_moon[3], pv_moon[4], pv_moon[5]])   # velocity of Moon
    as_M = comp_aM(jd1, jd2)

    w_0M = comp_w0M(jd1, jd2)   # Newtonian potential

    rs_M = xs - xs_M   # position relative to Moon

    # Calculate Y-x*
    PDY = L_B / (1 - L_B) * rs_M + 1 / (1 - L_B) * 1 / c**2 * (
        1/2 * np.dot(v_M, rs_M) * v_M + w_0M * rs_M
        + np.dot(as_M, rs_M) * rs_M - 1/2 * as_M * np.dot(rs_M, rs_M))
    return PDY


# (TDB, xs) to (TCL, Ys)

def TDB2TCL(jd1, jd2, xs):
    # time transformation
    dt = FLDTE(jd1, jd2) + FLPD(jd1, jd2, xs)
    TCL1 = jd1 + int(dt / day)
    TCL2 = jd2 + dt / day - int(dt / day)

    # space transformation
    dx = FPDY(jd1, jd2, xs)
    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])
    Y = xs - xs_M + dx

    return TCL1, TCL2, Y


# TCL-TDB


# Calculation Notes:
# The transformation from (TCL, Y) to (TDB, x*) adopts an iterative algorithm.
# The iterative error precisions for time and space transformations are both
# optional parameters, with default values of 1 nanosecond and 1 millimeter, respectively.


# Delta_t: time error (s), Delta_x: positioin error (km)
def TCL2TDB(jd1, jd2, Y, Delta_t=10**(-9), Delta_x=10**(-6)):
    def tcl2tdb(jdt1, jdt2, xsx):
        pv_moon = eph.compute_unit(jdt1, jdt2,
                                   NaifId.MOON,
                                   NaifId.SOLAR_SYSTEM_BARYCENTER,
                                   constants_kms)
        xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])

        # time transformation
        dt = FLDTE(jdt1, jdt2) + FLPD(jdt1, jdt2, xsx)
        TDBn1 = jd1 - int(dt / day)
        TDBn2 = jd2 - dt / day + int(dt / day)

        # space transformation
        dx = FPDY(jdt1, jdt2, xsx)
        xsn = Y + xs_M - dx
        return TDBn1, TDBn2, xsn

    # Initial settings, facilitating the start of the cycle
    dtz = 1000
    dxz = 1

    pv_moon = eph.compute_unit(jd1, jd2,
                               NaifId.MOON,
                               NaifId.SOLAR_SYSTEM_BARYCENTER,
                               constants_kms)
    xs_M = np.array([pv_moon[0], pv_moon[1], pv_moon[2]])

    TDB1_0 = jd1
    TDB2_0 = jd2
    xs_0 = Y + xs_M

    while abs(dtz) > Delta_t or abs(dxz) > Delta_x:
        TDB1_1, TDB2_1, xs_1 = TDB1_0, TDB2_0, xs_0
        TDB1_0, TDB2_0, xs_0 = tcl2tdb(TDB1_1, TDB2_1, xs_1)
        dtz = ((TDB1_0 - TDB1_1) + (TDB2_0 - TDB2_1)) * day
        dxz = np.linalg.norm(xs_0 - xs_1)

    return TDB1_0, TDB2_0, xs_0


##############################################################################


##############################################################################

# TT-TCG


# Calculation Notes:
# According to the IAU resolutions, the transformation between (TT, X*) and (TCG, X)
# is a linear transformation, where the scale factor L_G is a defined constant.
# Meanwhile, the IAU stipulates that the two systems coincide at 00:00:00 TAI
# on January 1, 1977.


# 1977-01-01 00:00:00 TAI / 1977-01-01 00:00:32.184 TT
t_0 = 2443144.5003725  # Julian Days


def TCG2TT(jd1, jd2, X):
    # time transformation TT-TCG
    dt = -L_G * (jd1 - t_0 + jd2) * day
    TT1 = jd1 + int(dt * day**(-1))
    TT2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    Xs = (1 - L_G) * np.array(X)

    return TT1, TT2, Xs


def TT2TCG(jd1, jd2, Xs):
    # time transformation TCG-TT
    dt = L_G / (1 - L_G) * (jd1 - t_0 + jd2) * day
    TCG1 = jd1 + int(dt * day**(-1))
    TCG2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    X = np.array(Xs) * (1 - L_G)**(-1)

    return TCG1, TCG2, X


##############################################################################


##############################################################################

# TDB-TCB


# Calculation Notes:
# According to the IAU resolutions, the transformation between (TDB, x*) and (TCB,x)
# is a linear transformation, where the scale factor L_B is a defined constant.
# According to the IAU regulations, TCB coincides with TT and TCG at 00:00:00 TAI
# on January 1, 1977, while TDB differs from them by a value of TDB0.


# TDB_0
TDB0 = -6.55 * 10**(-5)


def TCB2TDB(jd1, jd2, x):
    # time transformation TDB-TCB
    dt = -L_B * (jd1 - t_0 + jd2) * day + TDB0
    TDB1 = jd1 + int(dt * day**(-1))
    TDB2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    xs = (1 - L_B) * np.array(x)

    return TDB1, TDB2, xs


def TDB2TCB(jd1, jd2, xs):
    # time transformation TCB-TDB
    dt = L_B / (1 - L_B) * (jd1 - t_0 + jd2) * day - TDB0 / (1 - L_B)
    TCB1 = jd1 + int(dt * day**(-1))
    TCB2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    x = np.array(xs) * (1 - L_B)**(-1)

    return TCB1, TCB2, x


##############################################################################


##############################################################################


# LRT-TCL


# Calculation Notes:
# Although the IAU adopted the definition of TCL in 2024, the lunar time (LT) has
# not yet been defined.
# The Lunar Reference Time (LRT) calculated in this function is actually a linear
# transformation of TCL, where the scale factor L_L is an optional parameter with
# a default value of 3.139814814814815e-11, corresponding to the equipotential
# surface of the lunar surface.
# If L_L is set to 0, then LT equals TCL.
# Regarding the setting of the time origin, it is also designed as an optional
# parameter in this function;
# the default value is that TCL coincides with TCB at 00:00:00 TAI on January 1, 1977.


def TCL2LRT(jd1, jd2, Y, L_L=3.1395795e-11, t_l0=t_0):
    # time transformation LRT-TCL
    dt = -L_L * (jd1 - t_l0 + jd2) * day
    LRT1 = jd1 + int(dt * day**(-1))
    LRT2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    Ys = (1 - L_L) * np.array(Y)

    return LRT1, LRT2, Ys


def LRT2TCL(jd1, jd2, Ys, L_L=3.1395795e-11, t_l0=t_0):
    # time transformation TCL-LRT
    dt = L_L / (1 - L_L) * (jd1 - t_l0 + jd2) * day
    TCL1 = jd1 + int(dt * day**(-1))
    TCL2 = jd2 + (dt * day**(-1) - int(dt * day**(-1)))

    # space transformation
    Y = np.array(Ys) * (1 - L_L)**(-1)

    return TCL1, TCL2, Y


##############################################################################


##############################################################################


# 1a: TT1, TT2, Xs = TCG_to_TT(jd1, jd2, X)
# 1b: TCG1, TCG2, X = TT_to_TCG(jd1, jd2, Xs)


# 2a: TDB1, TDB2, xs = TCB_to_TDB(jd1, jd2, x)
# 2b: TCB1, TCB2, x = TDB_to_TCB(jd1, jd2, xs)


# 3a: TT1, TT2, Xs = TDB_to_TT(jd1, jd2, xs)
# 3b: TDB1_0, TDB2_0, xs_0 = TT_to_TDB(jd1, jd2, Xs, Delta_t = 10**(-9), Delta_x = 10**(-6))


# 4a: TCL1, TCL2, Y = TDB_to_TCL(jd1, jd2, xs)
# 4b: TDB1_0, TDB2_0, xs_0 = TCL_to_TDB(jd1, jd2, Y, Delta_t = 10**(-9), Delta_x = 10**(-6))


# 5a: LRT1, LRT2, Ys = TCL_to_LRT(jd1, jd2, Y, L_L = 3.1395795e-11, t_l0 = t_0)
# 5b: TCL1, TCL2, Y = LRT_to_TCL(jd1, jd2, Ys, L_L = 3.1395795e-11, t_l0 = t_0)


##############################################################################


##############################################################################

# TCB-LRT


def TCB2LRT(jd1, jd2, x, L_L=3.1395795e-11, t_l0=t_0):
    # TCB to TDB
    TDB1, TDB2, xs = TCB2TDB(jd1, jd2, x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1, TDB2, xs)
    # TCL to LRT
    LRT1, LRT2, Ys = TCL2LRT(TCL1, TCL2, Y, L_L=L_L, t_l0=t_l0)

    return LRT1, LRT2, Ys


# LRT-TCB


def LRT2TCB(jd1, jd2, Ys, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # LRT to TCL
    TCL1, TCL2, Y = LRT2TCL(jd1, jd2, Ys, L_L=L_L, t_l0=t_l0)
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(TCL1, TCL2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCB
    TCB1, TCB2, x = TDB2TCB(TDB1_0, TDB2_0, xs_0)

    return TCB1, TCB2, x


##############################################################################


##############################################################################

# TCB-TCL


def TCB2TCL(jd1, jd2, x):
    # TCB to TDB
    TDB1, TDB2, xs = TCB2TDB(jd1, jd2, x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1, TDB2, xs)

    return TCL1, TCL2, Y


# TCL-TCB


def TCL2TCB(jd1, jd2, Y, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(jd1, jd2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCB
    TCB1, TCB2, x = TDB2TCB(TDB1_0, TDB2_0, xs_0)

    return TCB1, TCB2, x


##############################################################################


##############################################################################

# TDB-LRT


def TDB2LRT(jd1, jd2, xs, L_L=3.1395795e-11, t_l0=t_0):
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(jd1, jd2, xs)
    # TCL to LRT
    LRT1, LRT2, Ys = TCL2LRT(TCL1, TCL2, Y, L_L=3.1395795e-11, t_l0=t_l0)

    return LRT1, LRT2, Ys


# LRT-TDB


def LRT2TDB(jd1, jd2, Ys, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # LRT to TCL
    TCL1, TCL2, Y = LRT2TCL(jd1, jd2, Ys, L_L=L_L, t_l0=t_l0)
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(TCL1, TCL2, Y, Delta_t=Delta_t, Delta_x=Delta_x)

    return TDB1_0, TDB2_0, xs_0


##############################################################################


##############################################################################

# TCG-LRT


def TCG2LRT(jd1, jd2, X, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # TCG to TT
    TT1, TT2, Xs = TCG2TT(jd1, jd2, X)
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(TT1, TT2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1_0, TDB2_0, xs_0)
    # TCL to LRT
    LRT1, LRT2, Ys = TCL2LRT(TCL1, TCL2, Y, L_L=L_L, t_l0=t_l0)

    return LRT1, LRT2, Ys


# LRT-TCG


def LRT2TCG(jd1, jd2, Ys, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # LRT to TCL
    TCL1, TCL2, Y = LRT2TCL(jd1, jd2, Ys, L_L=L_L, t_l0=t_l0)
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(TCL1, TCL2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(TDB1_0, TDB2_0, xs_0)
    # TT to TCG
    TCG1, TCG2, X = TT2TCG(TT1, TT2, Xs)

    return TCG1, TCG2, X


##############################################################################


##############################################################################

# TCG-TCL


def TCG2TCL(jd1, jd2, X, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCG to TT
    TT1, TT2, Xs = TCG2TT(jd1, jd2, X)
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(TT1, TT2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1_0, TDB2_0, xs_0)

    return TCL1, TCL2, Y


# TCL-TCG


def TCL2TCG(jd1, jd2, Y, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(jd1, jd2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(TDB1_0, TDB2_0, xs_0)
    # TT to TCG
    TCG1, TCG2, X = TT2TCG(TT1, TT2, Xs)

    return TCG1, TCG2, X


##############################################################################


##############################################################################

# TCG-TCB


def TCG2TCB(jd1, jd2, X, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCG to TT
    TT1, TT2, Xs = TCG2TT(jd1, jd2, X)
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(TT1, TT2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCB
    TCB1, TCB2, x = TDB2TCB(TDB1_0, TDB2_0, xs_0)

    return TCB1, TCB2, x


# TCB-TCG


def TCB2TCG(jd1, jd2, x):
    # TCB to TDB
    TDB1, TDB2, xs = TCB2TDB(jd1, jd2, x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(TDB1, TDB2, xs)
    # TT to TCG
    TCG1, TCG2, X = TT2TCG(TT1, TT2, Xs)

    return TCG1, TCG2, X


##############################################################################


##############################################################################

# TCG-TDB


def TCG2TDB(jd1, jd2, X, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCG to TT
    TT1, TT2, Xs = TCG2TT(jd1, jd2, X)
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(TT1, TT2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)

    return TDB1_0, TDB2_0, xs_0


# TDB-TCG


def TDB2TCG(jd1, jd2, xs):
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(jd1, jd2, xs)
    # TT to TCG
    TCG1, TCG2, X = TT2TCG(TT1, TT2, Xs)

    return TCG1, TCG2, X


##############################################################################


##############################################################################

# TT-LRT


def TT2LRT(jd1, jd2, Xs, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(jd1, jd2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1_0, TDB2_0, xs_0)
    # TCL to LRT
    LRT1, LRT2, Ys = TCL2LRT(TCL1, TCL2, Y, L_L=L_L, t_l0=t_l0)

    return LRT1, LRT2, Ys


# LRT-TT


def LRT2TT(jd1, jd2, Ys, Delta_t=10**(-9), Delta_x=10**(-6), L_L=3.1395795e-11, t_l0=t_0):
    # LRT to TCL
    TCL1, TCL2, Y = LRT2TCL(jd1, jd2, Ys, L_L=L_L, t_l0=t_l0)
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(TCL1, TCL2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(TDB1_0, TDB2_0, xs_0)

    return TT1, TT2, Xs


##############################################################################


##############################################################################

# TT-TCL


def TT2TCL(jd1, jd2, Xs, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(jd1, jd2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCL
    TCL1, TCL2, Y = TDB2TCL(TDB1_0, TDB2_0, xs_0)

    return TCL1, TCL2, Y


# TCL-TT


def TCL2TT(jd1, jd2, Y, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TCL to TDB
    TDB1_0, TDB2_0, xs_0 = TCL2TDB(jd1, jd2, Y, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(TDB1_0, TDB2_0, xs_0)

    return TT1, TT2, Xs


##############################################################################


##############################################################################

# TT-TCB


def TT2TCB(jd1, jd2, Xs, Delta_t=10**(-9), Delta_x=10**(-6)):
    # TT to TDB
    TDB1_0, TDB2_0, xs_0 = TT2TDB(jd1, jd2, Xs, Delta_t=Delta_t, Delta_x=Delta_x)
    # TDB to TCB
    TCB1, TCB2, x = TDB2TCB(TDB1_0, TDB2_0, xs_0)

    return TCB1, TCB2, x


# TCB-TT


def TCB2TT(jd1, jd2, x):
    # TCB to TDB
    TDB1, TDB2, xs = TCB2TDB(jd1, jd2, x)
    # TDB to TT
    TT1, TT2, Xs = TDB2TT(jd1, jd2, xs)

    return TT1, TT2, Xs


##############################################################################
