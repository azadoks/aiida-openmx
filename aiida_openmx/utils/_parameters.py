import typing as ty
import numpy as np

class _BlockParameter:
    def __init__(self, tag, data, formatter):
        self.tag = tag
        self.data = data
        self.formatter = formatter

    def __str__(self):
        return self.formatter(self.tag, self.data)


PARAMETERS = {
    'System.CurrentDirectory': {
         'type': str,
        'default': './'
    },
    'System.Name': {
        'type': str,
        'default': 'default'
    },
    'DATA.PATH': {
        'type': str,
        'default': '../DFT_DATA19'
    },
    'level.of.stdout': {
        'type': int,
        'default': 1,
        'lims': (1, 3)
    },
    'level.of.fileout': {
        'type': int,
        'default': 1,
        'lims': (0, 3)
    },
    # 'memory.usage.fileout': {
    #     'type': bool,
    #     'default': False
    # },
    # 'scf.ProExpn.VNA': {
    #     'type': bool,
    #     'default': 1
    # },
    # 'scf.BufferL.VNA': {
    #     'type': int,
    #     'default': 6
    # },
    # 'scf.RadialF.VNA': {
    #     'type': int,
    #     'default': 12
    # },
    'scf.energycutoff': {
        'type': float,
        'default': 150.,
        'unit': 'Ry'
    },
    # 'scf.MPI.tuned.grids': {
    #     'type': bool,
    #     'default': False
    # },
    'scf.Ngrid': {
        'type': ty.Iterable[int],
        'default': (0, 0, 0),
        'dims': (3,)
    },
    'Species.Number': {
        'type': int,
    },
    # 'scf.Hubbard.U': {
    #     'type': bool,
    #     'default': False
    # },
    # 'scf.DFTU.Type': {
    #     'type': int,
    #     'default': 1,
    #     'requires': {
    #         'scf.Hubbard.U': True
    #     }
    # },
    # 'scf.Yukawa': {
    #     'type': bool,
    #     'default': 0,
    #     'requires': {
    #         'scf.Hubbard.U': 2
    #     }
    # },
    # 'scf.dc.Type': {
    #     'type': str,
    #     'default': 'sFLL',
    #     'options': ('SFLL', 'sAMF', 'cFLL', 'cAMF'),
    #     'requires': {
    #         'scf.Hubbard.U': 1,
    #         'scf.DFTU.Type': 2
    #     }
    # },
    # 'scf.Slater.Ratio': {
    #     'type': float,
    #     'default': 0.625,
    #     'requires': {
    #         'scf.Hubbard.U': 1,
    #         'scf.DFTU.Type': 2
    #     }
    # },
    # 'scf.Hubbard.Occupation': {
    #     'type': str,
    #     'default': 'DUAL',
    #     'options': ('DUAL', 'ONSITE', 'FULL')
    # },
    # 'orbitalOpt.Method': {
    #     'type': str,
    #     'default': 'OFF',
    #     'options': ('OFF', 'Atoms', 'Species', 'Atoms2', 'Species2')
    # },
    'Definition.of.Atomic.Species': {},                                   # TODO
    'MD.Type': {
        'type':
        str,
        'default':
        'NOMD',
        'options':
        ('NOMD', 'NVE', 'NVT_VS', 'Opt', 'EF', 'BFGS', 'RF', 'DIIS', 'NVT_NH',
         'Opt_LBFGS', 'NVT_VS2', 'EvsLC', 'NEB', 'NVT_VS4', 'NVT_Langevin',
         'DF', 'OptC1', 'OptC2', 'OptC3', 'OptC4', 'OptC5', 'RFC1', 'RFC2',
         'RFC3', 'RFC4', 'RFC5', 'NPT_VS_PR', 'NPT_VS_WV', 'NPT_NH_PR',
         'NPT_NH_WV', 'RFC6', 'RFC7', 'OptC6', 'OptC7'),
    },
    'MD.maxIter': {  # Note: must be 7 if MD.Type == 'DF' (delta-factor)
        'type': int,
        'default': 1,
        'lims': (1, np.inf)
    },
    # 'MD.Current.Iter': {
    #     'type': int,
    #     'default': 0
    # },
    'MD.TimeStep': {
        'type': float,
        'default': 0.5,
        'lims': (0.0, np.inf),
        'unit': 'fs'
    },
    'MD.Opt.criterion': {
        'type': float,
        'default': 0.0003
    },
    'MD.Opt.DIIS.History': {
        'type': int,
        'default': 3,
        'lims': (0, 19)  # Not sure if 0 is a lower limit
    },
    'MD.Opt.StartDIIS': {
        'type': int,
        'default': 5,
    },
    'MD.Opt.EveryDIIS': {
        'type': int,
        'default': 200
    },
    # 'MD.EvsLC.Step': {
    #     'type': float,
    #     'default': 0.4
    # },
    # 'MD.EvsLC.flag': {
    #     'type': ty.Iterable[int],
    #     'default': (1, 1, 1),
    #     'dims': (3, )
    # },
    # 'MD.Out.ABC': {
    #     'type': bool,
    #     'default': False
    # },
    # 'MD.Opt.Init.Hessian': {
    #     'type': str,
    #     'default': 'Schlegel',
    #     'options': ('Schlegel', 'iden', 'FF')
    # },
    # 'MD.TempControl': {},
    # 'MD.CellPressureControl': {},
    # 'NH.Mass.HeatBath': {
    #     'type': float,
    #     'default': 20.0
    # },
    # 'NPT.Mass.Barostat': {
    #     'type': float,
    #     'default': 0.0,
    #     'unit': '???'
    # },
    # 'MD.TempTolerance': {
    #     'type': float,
    #     'default': 100.0,
    #     'unit': 'K'  # Guess
    # },
    # 'NPT.LatticeRestriction': {
    #     'type': str,
    #     'default': 'none',
    #     'options': ('none', 'cubic', 'ortho')
    # },
    # 'Langevin.Friction.Factor': {
    #     'type': float,
    #     'default': 0.001,
    # },
    # 'NPT.WV.F0': {},
    # 'LNO.flag': {
    #     'type': bool,
    #     'default':
    #     False  # set to True if scf.EigenvalueSolver in ['DC-LNO', 'Cluster-LNO']
    # },
    'scf.EigenvalueSolver': {
        'type':
        str,
        'default':
        'Band',  # AZ: I think this is best as the default
        'options': ('Cluster', 'Band', 'NEGF', 'DC', 'Cluster-DIIS',
                      'Krylov', 'Cluster2', 'EGAC', 'DC-LNO', 'Cluster-LNO')
    },
    # 'scf.lapack.dste': {
    #     'type': str,
    #     'default': 'dstevx',
    #     'options': ('dstevx', 'dstegr', 'dstedc', 'dsteqr')
    # },
    # 'scf.eigen.lib': {
    #     'type': str,
    #     'default': 'elpa1',
    #     'options': ('elpa1', 'lapack', 'elpa2')
    # },
    # 'scf.dclno.threading': {
    #     'type': bool,
    #     'default': False
    # },
    'scf.MP.criterion': {
        'type': float,
        'default': 1e-5
    },
    'scf.Generation.Kpoint': {
        'type': str,
        'default': 'REGULAR',
        'options': ('REGULAR', 'MP')  # MP can't be used with scf.EigenvalueSolver = 'NEGF'
    },
    # 'FT.files.save': {
    #     'type': bool,
    #     'default': False
    # },
    # 'FT.files.read': {
    #     'type': bool,
    #     'default': False
    # },
    'scf.XcType': {
        'type': str,
        'default': 'LDA',
        'options': ('LDA', 'LSDA-CA', 'LSDA-PW', 'GGA-PBE', 'EXX-TEST')
    },
    # 'scf.SpinPolarization': {
    #     'type': str,
    #     'default': 'Off',
    #     'options': ('Off', 'On', 'NC')
    # },
    # 'scf.Constraint.NC.Spin': {
    #     'type': str,
    #     'default': 'off',
    #     'options': ('off', 'on', 'on2')
    # },
    # 'scf.Constraint.NC.Spin.V': {
    #     'type': float,
    #     'default': 0.,
    #     'unit': 'eV'
    # },
    # 'scf.SpinOrbit.Coupling': {
    #     'type': bool,
    #     'default': False,
    #     'requires': {'scf.SpinPolarization': 'NC'}
    # },
    # 'scf.SO.factor': {},
    # 'scf.partialCoreCorrection': {
    #     'type': bool,
    #     'default': True,
    #     'options': (True,)
    # },
    # 'scf.pcc.opencore': {},
    # 'scf.NC.Zeeman.Spin': {
    #     'type': bool,
    #     'default': False,
    #     'requires': {'scf.SpinPolarization': 'NC',
    #                  'scf.Hubbard.Occupation': 'dual',
    #                  'scf.SpinOrbit.Coupling': True}
    # },
    # 'scf.NC.Mag.Field.Spin': {
    #     'type': float,
    #     'default': 0.,
    #     'unit': 'T'
    # },
    # 'scf.NC.Zeeman.Orbital': {
    #     'type': bool,
    #     'default': False
    # },
    # 'scf.NC.Mag.Field.Orbital': {
    #     'type': float,
    #     'default': 0.,
    #     'unit': 'T'
    # },
    'scf.Kgrid': {
        'type': ty.Iterable[int],
        'default': (4, 4, 4),
        'dim': (3,),
        'lims': (1, np.inf)
    },
    'scf.ElectronicTemperature': {
        'type': float,
        'default': 300.,
        'unit': 'K'  # E_temp = E_temp / ev2Hartree; ???
    },
    'scf.Mixing.Type': {
        'type': str,
        'default': 'Simple',
        'options': ('Simple', 'RMM-DIIS', 'GR-Pulay', 'Kerker', 'RMM-DIISK', 'RMM-DIISH', 'RMM-ADIIS', 'RMM=DIISV')
    },
    'scf.Init.Mixing.Weight': {
        'type': float,
        'default': 0.3
    },
    'scf.Min.Mixing.Weight': {
        'type': float,
        'default': 0.001
    },
    'scf.Max.Mixing.Weight': {
        'type': float,
        'default': 0.4        
    },
    # 'scf.Kerker.factor': {  # If not set explicitly (left as default -1.), will be set automatically
    #     'type': float,
    #     'default': -1.
    # },
    'scf.Mixing.History': {
        'type': int,
        'default': 5
    },
    'scf.Mixing.StartPulay': {
        'type': int,
        'default': 6
    },
    'scf.Mixing.EveryPulay': {
        'type': int,
        'default': 1
    },
    # 'scf.ExtCharge.History': {
    #     'type': int,
    #     'default': 3
    # },
    # 'scf.Mixing.Control.Temp': {
    #     'type': bool,
    #     'default': False
    # },
    'scf.criterion': {
        'type': float,
        'default': 1e-6,
        'lims': (0, np.inf)
    },
    # 'scf.system.charge': {
    #     'type': float,
    #     'default': 0.
    # },
    # 'CDDF.start': {
    #     'type': bool,
    #     'default': 0
    # },
    # 'CDDF.FWHM': {
    #     'type': float,
    #     'default': 0.2,
    #     'unit': 'eV'
    # },
    # 'CDDF.maximum_energy': {
    #     'type': float,
    #     'default': 10.,
    #     'unit': 'eV'
    # },
    # 'CDDF.minimum_energy': {
    #     'type': float,
    #     'default': 0.,
    #     'unit': 'eV'
    # },
    # 'CDDF.additional_maximum_energy': {
    #     'type': float,
    #     'default': 0.,
    #     'unit': 'eV'
    # },
    # 'CDDF.frequency.grid.total_number': {
    #     'type': int,
    #     'default': 10_000
    # },
    # 'CDDF.maximum_unoccupied_state': {  # Acts as a bool
    #     'type': int,
    #     'default': 0,
    #     'lims': (0, 1)
    # },
    # 'CDDF.material_type': {
    #     'type': int,
    #     'default': 0,
    #     'lims': (0, 1)  # insulator, metal
    # },
    # 'ESM.switch': {},
    # 'ESM.wall.switch': {},
    # 'ESM.direction': {},
    # 'ESM.potential.diff': {},
    # 'ESM.wall.position': {},
    # 'ESM.wall.eight': {},
    # 'ESM.buffer.range': {},
    # 'MD.Artificial_Force': {},
    # 'MD.Artifical_Grad': {},
    # 'geoopt.restart': {
    #     'type': bool,
    #     'default': False
    # },
    'Atoms.Number': {
        'type': int
    },
    'Atoms.SpeciesAndCoordinates.Unit': {
        'type': str,
        'default': 'Ang',
        'options': ('Ang', 'AU', 'FRAC')
    },
    'Atoms.SpeciesAndCoordinates': {},                                    # TODO
    'Atoms.Unitvectors.Unit': {
        'type': str,
        'default': 'Ang',
        'options': ('Ang', 'AU')
    },
    'Atoms.Unitvectors': {},                                              # TODO
    # 'Atoms.Unitvectors.Velocity': {},
    # 'orderN.LNO.Occ.Cutoff': {},
    # 'orderN.LNO.Buffer': {},
    # 'LNOs.Num': {},
    # 'scf.core.hole': {
    #     'type': bool,
    #     'default': False
    # },
    # 'scf.coulomb.cutoff': {
    #     'type': str,
    #     'default': 'off',
    #     'options': ('off', 'on')
    # },
    # 'CLE.Type': {},
    # 'CLE.Val.Window': {},
    # 'CLE.Con.Window': {},
    # 'scf.dftD': {},
    # 'version.dftD': {},
    # 'DFTD.Unit': {},
    # 'DFTD.rcut_dftD': {},
    # 'DFTD.d': {},
    # 'DFTD.scale6': {},
    # 'DFTD.InDirection': {},
    # 'DFTD.periodicity': {},
    # 'DFTD3.damp': {},
    # 'DFTD.sr6': {},
    # 'DFTD.a1': {},
    # 'DFTD.a2': {},
    # 'DFTD.scale8': {},
    # 'DFTD.sr6': {},
    # 'DFTD.a1': {},
    # 'DFTD.a2': {},
    # 'DFTD.cncut_dftD': {},
    # 'MD.Fixed.Cell.Vectors': {},
    # 'MD.Fixed.XYZ': {},
    # 'MD.Init.Velocity': {},
    # 'MD.Init.Velocity.Prev': {},
    # 'NH.R': {},
    # 'NH.nzeta': {},
    # 'NH.czeta': {},
    # 'MD.num.AtomGroup': {},
    # 'Hubbard.U.values': {},
    # 'Hund.J.values': {},
    'scf.maxIter': {
        'type': int,
        'default': 40,
        'lims': (1, np.inf)
    },
    # 'scf.Npoles.ON2': {},
    # 'scf.Npoles.EGAC': {},
    # 'scf.DIIS.History.EGAC': {},
    # 'scf.AC.flag.EGAC': {},
    # 'scf.GF.EGAC': {},
    'Atoms.NetCharge': {
        'type': float,
        'default': 0.
    },
    'scf.restart': {
        'type': str,
        'default': 'off',
        'options': ('off', 'alloff', 'on', 'c2n')
    },
    'scf.restart.filename': {
        'type': str,
        'default': 'default'
    },
    # 'scf.Restart.Spin.Angle.Theta': {
    #     'type': float,
    #     'default': 0.
    # },
    # 'scf.Restart.Spin.Angle.Phi': {
    #     'type': float,
    #     'default': 0.
    # },
    # 'scf.Generalized.Bloch': {},
    # 'Spin.Spiral.Vector': {},
    'Band.dispersion': {
        'type': bool,
        'default': False
    },
    'Band.Nkpath': {
        'type': int,
        'default': 0
    },
    'Band.kpath.UnitCell': {},                                            # TODO
    'Band.kpath': {},                                                     # TODO
    '1DFFT.NumGridK': {
        'type': int,
        'default': 900
    },
    '1DFFT.EnergyCutoff': {
        'type': float,
        'default': 3600.
    },
    '1DFFT.NumGridR': {
        'type': int,
        'default': 900
    },
    # 'orbitalOpt.InitCoes': {},
    # 'orbitalOpt.scf.maxIter': {},
    # 'orbitalOpt.Opt.MaxIter': {},
    # 'orbitalOpt.per.MDIter': {},
    # 'orbitalOpt.criterion': {},
    # 'orbitalOpt.SD.step': {},
    # 'orbitalOpt.HistoryPulay': {},
    # 'orbitalOpt.StartPulay': {},
    # 'orbitalOpt.Force.Skip': {},
    # 'orbitalOpt.Opt.Method': {},
    # 'orderN.HoppingRanges': {},
    # 'orderN.NumHoppings': {},
    # 'orderN.EC.Sub.Dim': {},
    # 'orderN.KrylovH.order': {},
    # 'orderN.KrylovS.order': {},
    # 'orderN.Recalc.Buffer': {},
    # 'orderN.Exact.Inverse.S': {},
    # 'orderN.Expand.Core': {},
    # 'orderN.Inverse.S': {},
    # 'orderN.FNAN.SNAN': {},
    # 'orderN.RecursiveLevels': {},
    # 'orderN.TerminatorType': {},
    # 'orderN.InverseSolver': {},
    # 'orderN.InvRecursiveLevels': {},
    # 'orderN.ChargeDeviation': {},
    # 'orderN.InitChemPot': {},
    # 'orderN.AvNumTerminater': {},
    # 'orderN.NumPoles': {},
    # 'MO.fileout': {},
    # 'num.HOMOs': {},
    # 'num.LUMOs': {},
    # 'MO.Nkpoint': {},
    # 'MO.kpoint': {},
    # 'NBO.switch': {},
    # 'NAO.only': {},
    # 'NAO.threshold': {},
    # 'NBO.Num.CenterAtoms': {},
    # 'NBO.CenterAtoms': {},
    # 'NHO.fileout': {},
    # 'NBO.fileout': {},
    # 'NBO.SmallCell.Switch': {},
    # 'NBO.SmallCell': {},
    # 'Unfolding.Electronic.Band': {},
    # 'Unfolding.Reference.Vectors': {},
    # 'Unfolding.Referenceorigin': {},
    # 'Unfolding.LowerBound': {},
    # 'Unfolding.UpperBound': {},
    # 'Unfolding.Map': {},
    # 'Unfolding.Nkpoint': {},
    # 'Unfolding.desired_totalnkpt': {},
    # 'Unfolding.kpoint': {},
    # 'empty.occupation.flag': {},
    # 'empty.occupation.number': {},
    # 'empty.occupation.orbitals': {},
    # 'empty.states.flag': {},
    # 'empty.states.orbitals': {},
    # 'OutData.bin.flag': {},
    # 'CntOrb.fileout': {},
    # 'Num.CntOrb.Atoms': {},
    # 'Atoms.Cont.Orbitals': {},
    # 'scf.ElectricField': {},
    'Dos.fileout': {
        'type': bool,
        'default': False
    },
    'DosGauss.fileout': {
        'type': bool,
        'default': False
    },
    'DosGauss.Num.Mesh': {
        'type': int,
        'default': 200
    },
    'DosGauss.Width': {
        'type': bool,
        'default': 0.2,
        'unit': 'eV'
    },
    'FermiSurfer.fileout': {
        'type': bool,
        'default': False
    },
    'Dos.Erange': {
        'type': ty.Iterable[float],
        'default': (-20., 20.),
        'dim': (2,),
        'unit': 'eV'
    },
    'Dos.Kgrid': {
        'type': ty.Iterable[int],
        'default': (4, 4, 4),  # k-grid
        'dim': (3,)
    },
    # 'partial.charge': {},
    # 'partial.charge.energy.window': {},
    'HS.fileout': {
        'type': bool,
        'default': False
    },
    # 'Energy.Decomposition': {},
    # 'Voronoi.charge': {},
    # 'Voronoi.orbital.moment': {},
    # 'Wannier.Func.Calc': {},
    # 'Wannier90.fileout': {},
    # 'Wannier.Func.Num': {},
    # 'Wannier.Outer.Window.Bottom': {},
    # 'Wannier.Outer.Window.Top': {},
    # 'Wannier.Inner.Window.Bottom': {},
    # 'Wannier.Inner.Window.Top': {},
    # 'Wannier.Initial.Guess': {},
    # 'Wannier.Initial.Projectors.Unit': {},
    # 'Wannier.Initial.Projectors': {},
    # 'Wannier.Kgrid': {},
    # 'Wannier.MaxShells': {},
    # 'Wannier.Minimizing.Max.Steps': {},
    # 'Wannier.Function.Plot': {},
    # 'Wannier.Function.Plot.SuperCells': {},
    # 'Wannier.Dis.Mixing.Para': {},
    # 'Wannier.Dis.Conv.Criterion': {},
    # 'Wannier.Dis.SCF.Max.Steps': {},
    # 'Wannier.Minimizing.Scheme': {},
    # 'Wannier.Minimizing.StepLength': {},
    # 'Wannier.Minimizing.Secant.Steps': {},
    # 'Wannier.Minimizing.Secant.StepLength': {},
    # 'Wannier.Minimizing.Conv.Criterion': {},
    # 'Wannier.Output.kmesh': {},
    # 'Wannier.Readin.Overlap.Matrix': {},
    'scf.stress.tensor': {
        'type': bool,
        'default': False
    },
    # 'MD.applied.pressure': {},
    # 'MD.applied.pressure.flag': {},
    # 'Population.Analysis.AO.Wanniers': {}
}
