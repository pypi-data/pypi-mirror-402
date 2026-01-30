import gromologist as gml
import unittest
import os
import numpy as np


class PdbExtraTest(unittest.TestCase):

    def setUp(self) -> None:
        self.pdb = gml.Pdb('pentapeptide.pdb')

    def tearDown(self) -> None:
        del self.pdb

    def test_len_getitem(self):
        self.assertEqual(len(self.pdb), self.pdb.natoms)
        self.assertIsInstance(self.pdb[0], gml.Atom)

    def test_add_remark(self):
        orig = len(self.pdb.remarks)
        self.pdb.add_remark("unit-test")
        self.assertEqual(len(self.pdb.remarks), orig + 1)
        self.assertIn("unit-test", self.pdb.remarks[-1])

    def test_keep_altloc(self):
        orig = self.pdb.natoms
        self.pdb.atoms[0].altloc = 'A'
        self.pdb.atoms[1].altloc = 'B'
        self.pdb.keep_altloc('A')
        self.assertEqual(self.pdb.natoms, orig - 1)
        self.assertNotIn('B', {a.altloc for a in self.pdb.atoms})
        self.assertEqual(self.pdb.altloc, 'A')

    def test_from_text_roundtrip(self):
        tmp = 'tmp_roundtrip.pdb'
        self.pdb.save_pdb(tmp)
        with open(tmp) as handle:
            text = handle.read()
        new_pdb = gml.Pdb.from_text(text)
        os.remove(tmp)
        self.assertEqual(new_pdb.natoms, self.pdb.natoms)
        self.assertEqual(new_pdb.atoms[0].atomname, self.pdb.atoms[0].atomname)

    def test_insert_from(self):
        other = self.pdb.from_selection('resid 2')
        orig_natoms = self.pdb.natoms
        last_res1 = self.pdb.get_atom_indices('resid 1')[-1]
        self.pdb.insert_from(other, selection='all', after='resid 1')
        self.assertEqual(self.pdb.natoms, orig_natoms + other.natoms)
        self.assertTrue(np.allclose(self.pdb.atoms[last_res1 + 1].coords, other.atoms[0].coords))

    def test_seq_from_struct(self):
        self.pdb.add_chains()
        seq = self.pdb.seq_from_struct()
        self.assertEqual(seq, {'A': 'ALFIV'})

    def test_get_atom_indices_formats(self):
        indices = self.pdb.get_atom_indices('name CA')
        self.assertEqual(len(indices), 5)
        plumed = self.pdb.get_atom_indices('name CA', as_plumed=True)
        self.assertTrue(plumed.startswith("ATOMS="))
        self.assertEqual(len(plumed.split('=')[1].split(',')), 5)
        ndx = self.pdb.get_atom_indices('name CA', as_ndx=True)
        numbers = [int(x) for x in ndx.split() if x.isdigit()]
        self.assertEqual(len(numbers), 5)
        self.assertEqual(sorted(numbers), [i + 1 for i in indices])

    def test_get_atom_index_and_get_atom(self):
        self.assertEqual(self.pdb.get_atom_index('serial 1'), 0)
        atom = self.pdb.get_atom('serial 1')
        self.assertEqual(atom.serial, 1)
        self.assertEqual(atom.atomname, 'N')

    def test_same_residue_as(self):
        res1_indices = set(self.pdb.get_atom_indices('resid 1'))
        same = self.pdb.same_residue_as([0])
        self.assertEqual(res1_indices, same)

    def test_within_and_n_closest(self):
        within = self.pdb.within([0], 0.0, nopbc=True)
        self.assertEqual(within, {0})
        closest = self.pdb.n_closest('serial 1', 'serial 1', 1)
        self.assertEqual(closest, [0])

    def test_translate(self):
        orig = self.pdb.atoms[0].coords.copy()
        self.pdb.translate([1.0, -2.0, 0.5])
        self.assertTrue(np.allclose(self.pdb.atoms[0].coords, orig + np.array([1.0, -2.0, 0.5])))

    def test_renumber_residues(self):
        self.pdb.renumber_residues(offset=10)
        resnums = sorted({a.resnum for a in self.pdb.atoms})
        self.assertEqual(resnums[0], 10)
        self.assertEqual(resnums[-1], 14)

    def test_save_from_selection(self):
        tmp = 'tmp_sel.pdb'
        self.pdb.save_from_selection('resid 1', outname=tmp, renum=True)
        self.assertTrue(os.path.exists(tmp))
        os.remove(tmp)


if __name__ == "__main__":
    unittest.main()
