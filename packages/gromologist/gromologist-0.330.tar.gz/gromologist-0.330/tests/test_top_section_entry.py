import gromologist as gml
import unittest
import os
import copy


class TopExtraTest(unittest.TestCase):

    def setUp(self) -> None:
        self.top = gml.Top('pentapeptide.top')

    def tearDown(self) -> None:
        del self.top

    def test_repr_and_atoms_count(self):
        self.assertIn("Topology with", repr(self.top))
        self.assertEqual(len(self.top.atoms), self.top.natoms)

    def test_clone_isolated(self):
        clone = self.top.clone()
        clone.molecules[0].atoms[0].charge = 123.0
        self.assertNotEqual(clone.molecules[0].atoms[0].charge, self.top.molecules[0].atoms[0].charge)

    def test_defaults(self):
        defaults = self.top.defaults
        self.assertEqual(defaults['nbfunc'], 1)
        self.assertEqual(defaults['comb-rule'], 2)
        self.assertEqual(defaults['gen-pairs'], 'yes')
        self.assertEqual(defaults['fudgeLJ'], 1.0)
        self.assertEqual(defaults['fudgeQQ'], 1.0)

    def test_defined_atomtypes(self):
        first_type = self.top.molecules[0].atoms[0].type
        self.assertIn(first_type, self.top.defined_atomtypes)

    def test_select_atoms_and_get_atom(self):
        indices = self.top.select_atoms('name CA')
        self.assertEqual(len(indices), 5)
        atom = self.top.get_atom('name CA and resid 1')
        self.assertEqual(atom.atomname, 'CA')

    def test_map_property_on_structure(self):
        self.top.add_pdb('pentapeptide.pdb')
        self.top.map_property_on_structure(property='charge', field='beta')
        self.assertAlmostEqual(self.top.pdb.atoms[0].beta, self.top.atoms[0].charge)

    def test_save_top(self):
        tmp = 'tmp_saved.top'
        self.top.save_top(tmp)
        self.assertTrue(os.path.exists(tmp))
        with open(tmp) as handle:
            data = handle.read()
        self.assertIn('[ moleculetype ]', data)
        os.remove(tmp)


class SectionSubsectionEntryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.top = gml.Top('pentapeptide.top')
        self.mol = self.top.molecules[0]

    def tearDown(self) -> None:
        del self.mol
        del self.top

    def test_section_get_and_init_remove_subsection(self):
        self.assertTrue(self.mol.has_subsection('atoms'))
        atoms_sub = self.mol.get_subsection('atoms')
        self.assertIsInstance(atoms_sub, gml.SubsectionAtom)
        self.mol.init_subsection('position_restraints')
        self.assertTrue(self.mol.has_subsection('position_restraints'))
        self.mol.remove_subsection('position_restraints')
        self.assertFalse(self.mol.has_subsection('position_restraints'))

    def test_section_save_itp(self):
        tmp = 'tmp_mol.itp'
        self.mol.save_itp(tmp)
        self.assertTrue(os.path.exists(tmp))
        with open(tmp) as handle:
            data = handle.read()
        self.assertIn('[ moleculetype ]', data)
        os.remove(tmp)

    def test_sectionmol_properties(self):
        self.assertEqual(self.mol.natoms, 87)
        self.assertEqual(self.mol.nmols, 1)
        self.assertEqual(len(self.mol.residues), 5)
        self.assertGreater(self.mol.mass, 0.0)

    def test_sectionmol_atomtypes_and_flags(self):
        self.assertIn(self.mol.atoms[0].type, self.mol.atomtypes)
        self.assertTrue(self.mol.is_protein)
        self.assertFalse(self.mol.is_water)
        self.assertFalse(self.mol.is_nucleic)

    def test_sectionmol_select_and_get_atom(self):
        indices = self.mol.select_atoms('name CA')
        self.assertEqual(len(indices), 5)
        atom = self.mol.get_atom('name CA and resid 1')
        self.assertEqual(atom.atomname, 'CA')

    def test_sectionmol_set_type(self):
        self.mol.set_type(type_to_set='DUM', atomname='CA', resid=1)
        atom = self.mol.get_atom('name CA and resid 1')
        self.assertEqual(atom.type, 'DUM')

    def test_sectionmol_rename(self):
        self.mol.rename('TEST')
        self.assertEqual(self.mol.mol_name, 'TEST')

    def test_sectionmol_add_posres(self):
        self.mol.add_posres(keyword=None, value=200.0, selection='name CA')
        self.assertTrue(self.mol.has_subsection('position_restraints'))
        sub = self.mol.get_subsection('position_restraints')
        self.assertGreater(len(sub.entries_bonded), 0)

    def test_sectionmol_bonds_property(self):
        bonds = self.mol.bonds
        self.assertGreater(len(bonds), 0)
        self.assertEqual(len(bonds[0]), 2)

    def test_subsection_add_remove_entries(self):
        sub = self.mol.bonds_section
        entry = gml.EntryBonded("1 2 1", sub)
        orig_len = len(sub.entries)
        sub.add_entry(entry)
        self.assertEqual(len(sub.entries), orig_len + 1)
        self.assertIs(entry.subsection, sub)
        sub.remove_entry(entry)
        self.assertEqual(len(sub.entries), orig_len)

    def test_subsection_iter_and_len(self):
        sub = self.mol.bonds_section
        self.assertEqual(len(sub), len(sub.entries))
        self.assertEqual(list(iter(sub)), sub.entries)

    def test_subsectionbonded_change_interaction_type(self):
        sub = gml.SubsectionBonded(['[ bonds ]', '1 2 1', '2 3 1'], self.mol)
        sub.change_interaction_type('1', '2')
        self.assertTrue(all(e.interaction_type == '2' for e in sub.entries_bonded))

    def test_subsectionparam_merge_and_get_entries(self):
        sub = self.top.parameters.get_subsection('bondtypes')
        entry = sub.entries_param[0]
        matches = sub.get_entries_by_types(*entry.types)
        self.assertIn(entry, matches)
        merged = sub + sub
        self.assertIsInstance(merged, gml.SubsectionParam)
        self.assertEqual(merged.header, sub.header)
        self.assertGreater(len(merged.entries_param), len(sub.entries_param))

    def test_entry_basics(self):
        sub = self.mol.get_subsection('atoms')
        comment = gml.Entry("; comment", sub)
        empty = gml.Entry("", sub)
        header = gml.Entry("[ atoms ]", sub)
        self.assertTrue(comment.is_comment)
        self.assertTrue(comment)
        self.assertFalse(bool(empty))
        self.assertTrue(header.is_header())

    def test_entry_infer_type_and_float_fmt(self):
        self.assertEqual(gml.Entry.infer_type("1"), int)
        self.assertEqual(gml.Entry.infer_type("1.5"), float)
        self.assertEqual(gml.Entry.infer_type("ABC"), str)
        fmt = gml.Entry.float_fmt(1.234567)
        formatted = fmt.format(1.234567).strip()
        self.assertTrue(formatted.startswith("1.234"))

    def test_entrybonded_parse(self):
        sub = self.mol.bonds_section
        entry = gml.EntryBonded("1 2 1", sub)
        self.assertEqual(entry.atom_numbers, (1, 2))
        self.assertEqual(entry.interaction_type, '1')

    def test_entryparam_match(self):
        sub = self.top.parameters.get_subsection('bondtypes')
        entry = sub.entries_param[0]
        self.assertTrue(entry.match(list(entry.types), entry.interaction_type))
        self.assertTrue(entry.match(list(entry.types[::-1]), entry.interaction_type))

    def test_entryatom_properties(self):
        atom = self.mol.atoms[0]
        hydrogen = next(a for a in self.mol.atoms if a.atomname.startswith('H'))
        self.assertEqual(atom.element, atom.atomname[0])
        self.assertFalse(atom.ish)
        self.assertTrue(hydrogen.ish)
        bonds = self.mol.list_bonds(by_num=True, returning=True)
        expected = [b for b in bonds if atom.num in b]
        self.assertEqual(len(atom.bound_atoms), len(expected))
        atom.add_alchemical_state('DUM', charge=0.1, mass=2.0)
        self.assertEqual(atom.type_b, 'DUM')
        self.assertEqual(atom.charge_b, 0.1)
        self.assertEqual(atom.mass_b, 2.0)
        atom2 = copy.deepcopy(atom)
        self.assertEqual(atom, atom2)


if __name__ == "__main__":
    unittest.main()
