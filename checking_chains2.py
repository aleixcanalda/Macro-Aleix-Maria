import sys
from classes import *
#from IOinterface.py import *
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Chain import Chain
from Bio.PDB.PDBIO import PDBIO
import random
import gzip
import re
from Bio import SeqIO
import os, glob
import argparse


parser = PDBParser(PERMISSIVE=1, QUIET=True)

def all_chains(PDB_files, verbose=False):
	""" Creating an object for every unique PDB chain. """

	unique_chain_list=[]
	id_set=set()
	if verbose:
		print("Processing PDB files and analyzing the chains")

	for file in PDB_files:
		for model in parser.get_structure("A",file): #Obtain the structures and iterate on all models
			chain_num = 0
			my_list = []
			for chain in model: #Obtain all chains from the models
				new_instance = MyChain(chain)
				letter = chain_id(id_set)
				#new_instance.id = letter #Change ID of the sequence
				#id_set.add(letter)
				chain_num += 1
				my_list.append(new_instance)

				#if unique_chain_list == []:
				#	unique_chain_list.append(new_instance) #First instance is appended to the list.

				#else:
				#	unique = True
				#	for instance in unique_chain_list:
						
				#		if instance.compare_sequence(new_instance) == True:
				#			unique = False
				#			break
							

			if chain_num != 2:
				sys.stderr.write("All PDB files must contain two chains.")
				
			unique_chain_list.append(my_list)


	return unique_chain_list
							


def chain_id(id_set):
	""" Function to create unique IDs """
	
	alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
				'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'BB',
				'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'II', 'JJ', 'KK', 'LL', 'MM', 'NN',
				'OO', 'PP', 'QQ', 'RR', 'SS', 'TT', 'UU', 'VV', 'WW', 'XX', 'YY', 'ZZ']
	for letter in alphabet:
		if letter not in id_set:
			return letter

def get_interactions_dict(unique_chain_list, verbose=False):
	""" 
	Obtain the dictionary of interactions among all chains
	The dictionary will look as follows:
	'Chain1.id' = [[Chain1, Chain2 that interacts with chain 1],[Chain1,Chain3],...] 
	"""
	if verbose:
		sys.stderr.write("Obtaining the interactions dictionary.")

	interactions_dict = {}
	
	for pair in unique_chain_list:
		chain1 = pair[0]
		chain2 = pair[1]
		
		interact_1, interact_2 = chain1.interactions(chain2)
		if interact_1 == set() and interact_2 == set():
			continue

		if interactions_dict == {}:
			interactions_dict[chain1.id]= [[chain1, chain2]]
			interactions_dict[chain2.id]= [[chain2, chain1]]
		else:
			checking1 = False
			checking2 = False
			for key in interactions_dict.keys():
				check1 = chain1.compare_sequence(interactions_dict[key][0][0]) ##Dilemes de l'Aleix 2.0 (igual coordenada, igual seqüència)
				if check1:
					interactions_dict[key].append([chain1, chain2])
					checking1 = True
				check2 = chain2.compare_sequence(interactions_dict[key][0][0])
				if check2:
					interactions_dict[key].append([chain2, chain1])
					checking2 = True
			if checking1 == False: ##WHAT WHAT Dilemes de la MAria 1.0 (per que check1 ja no es true?)
				interactions_dict[chain1.id]= [[chain1, chain2]]
			if checking2 == False:
				interactions_dict[chain2.id]= [[chain2, chain1]]
			print(interactions_dict)
	
	return interactions_dict

	"""
	for chain1 in unique_chain_list:

		interactions_dict[chain1.id] = []
	
		for chain2 in unique_chain_list:

			if chain1.id == chain2.id:
				continue

			interact_1, interact_2 = chain1.interactions(chain2)

			if interact_1 == set() and interact_2 == set():
				continue

			else:

				interactions_dict[chain1.id].append(chain2.id)

	"""

def start_model(interactions_dict,verbose=False):
	"""Choosing the chain with most interactions as the starting model of the macrocomplex"""

	model = Model("A") #Create new instance of class Model
	
	if verbose:
		sys.stderr.write("Deciding the starting model.")

	most_inter = 0

	for chain in interactions_dict.keys():

		chain_inter = len(interactions_dict[chain])

		if chain_inter > most_inter:

			most_inter = chain_inter

			starting_chain = chain
	model.add(interactions_dict[starting_chain][0][0]) #We add the chain with most interactions to the model.

	model.add(interactions_dict[starting_chain][0][1])

	#second_chain = False

	"""
	for inter in interactions_dict[starting_chain]: #Search for a second chains that interacts with the starting chain.
		if second_chain == True:
			break
		for file in pdbfiles:
			if inter in str(file) and starting_chain in str(file): #If there is an input file with the interaction of these two chains, we add it to the model
				model.add(next(x for x in unique_chains_list if x.id == inter))
				second_chain = True
				break
	"""
	return model

def equal_length_chains(chain1, chain2):
	"""Equaling the lengths of two chains."""
	
	atoms1 = sorted(chain1.get_atoms())
	atoms2 = sorted(chain2.get_atoms())

	if len(atoms1) > len(atoms2):
		return atoms1[:len(atoms2)], atoms2

	elif len(atoms1) < len(atoms2):
		return atoms1, atoms2[:len(atoms1)]
	
	else:
		return atoms1, atoms2


def clashes(chain_atoms, model):
	""" Calculates the clashes between two chains and returns whether the claches are in more than 5% of the atoms."""
	
	print("Hi")
	backbone = {"CA", "C1\'"}
	chain_atoms = [a for a in chain_atoms if a.id in backbone]  # Gets only the backbone atoms
	model_atoms = [a for a in model.get_atoms() if a.id in backbone]
	Nsearch = Bio.PDB.NeighborSearch(model_atoms)
	
	clash_count = 0
	for atoms in chain_atoms:
		clash = Nsearch.search(atoms.coord, 2) #Returns the atoms that clash
		if clash != []: #If there are atoms that clash, add 1 the the clash counter
			clash_count += 1
	print(clash_count/len(chain_atoms))
	if clash_count/len(chain_atoms) >= 0.05: #If the clashes are more than 5% of the atoms
		return True
	else:
		return False

	
def superimpose(unique_chains_list,interactions_dict, verbose=False):
	""" """
	model = start_model(int_dict,verbose)
	chain1, chain2 = model.get_chains()
	chain_in_model = [chain1.id,chain2.id]
	print(int_dict)
	print(chain1)
	print(chain2)
	#random.shuffle(unique_chains_list)
	n = 2
	while n<len(int_dict.keys()):
		for chain in interactions_dict.keys():
			if chain in chain_in_model:
				continue
			print("looking at:%s"%(chain))	
			not_added = True
			#shuffle(chain_in_model): if we want to make more models, we should shuffle the chainsin the model so the chains are superimposed to different chains.
			for chainin in chain_in_model:
				
				for chain_model, chain_interact in interactions_dict[chainin]: #if our chain interacts with a chain inside the complex
					if chain_interact.id == chain:
						chaininin = [x for x in model.get_chains() if x.id == chainin]
						print(chaininin)
						newChain, modelChain = equal_length_chains(chain_model, chaininin[0])
						#Equaling the lentgh of the chains (needed for the Superimposer)
						superimpose = Bio.PDB.Superimposer() #Create a Superimposer instance
						superimpose.set_atoms(modelChain, newChain) #Create superimposition matrix
						chain_copy = chain_interact.copy() #Copy the chain so that we still keep the original version.
						chain_copy.id = chain
						superimpose.apply(chain_copy) #Apply the superposition matrix
						chain_atoms = sorted(chain_copy.get_atoms())
					
						if clashes(chain_atoms, model) == True:
							continue
						
						else:
							chain_copy.parent = None
							print(chain_copy)
							model.add(chain_copy)
							not_added = False
							chain_in_model.append(chain)
							print(chain_in_model)
							n += 1

							if verbose:
								print("%s sucessfully added to the model" %chain)

							break
						
			if verbose and not_added:
				print("%s could not be added to the model" %chain)
			
			#n += 1
			#chain_in_model.append(chain.id)
	return model
			
def save_PDB(model, output_path, verbose=False):
	if verbose:
		print("Saving model")
	io = PDBIO()
	io.set_structure(model)
	io.save("model.pdb")
	
if __name__ == "__main__":
	#pdb = open("1gzx_A_B.pdb")

	#files=["1gzx_A_B.pdb","1gzx_A_C.pdb","1gzx_A_D.pdb"]

	#parser = PDBParser(PERMISSIVE=1, QUIET=True)

	#chains = []

	#struct = parser.get_structure(file="1gzx_A_B.pdb",id="A")
	#for model in struct:
	#	for chain in model:
	#		ch = MyChain(chain)
	#		chains.append(ch)
	fasp = re.compile('.pdb$|.pdb.gz$')
	path = "/home/aleix/Documents/MSc_Bioinfo/PYT/examples/5fj8"
	final_prots_files = []
	try:
		if os.path.isdir(path):
			prots_files = [f for f in os.listdir(path) if fasp.search(f) is not None]
			os.chdir(path)
	except:
		raise OSError('No directory could be read')

	for file in prots_files:
		if file.endswith('.gz'):
			with gzip.open(file) as fd:
				for line in fd:
					chains = []
					if line.startswith("ATOM"):
						pdb = line.split()
						chain = pdb[4]
						if chain not in chains:
							chains.append(chain)
		else:
			with open(file) as fd:
				chains=[]
				for line in fd:
					if line.startswith("ATOM"):
						pdb = line.split()
						chain = pdb[4]
						if chain not in chains:
							chains.append(chain)

		if re.search(r'\w+_%s_%s'%('|'.join(chains),'|'.join(chains)),file) is not None:
			final_prots_files.append(file)
		else:
			raise ValueError('File name %s is not correct'%(file))
	unique_chain_list = all_chains(final_prots_files)
	print(unique_chain_list)
	dict_int = get_interactions_dict(unique_chain_list)
	#print(dict_int)
	

	#start_chain = start_model(dict_int)
	model = superimpose(unique_chain_list,dict_int)
	print(model)
	#save_PDB(model, "home/maria/master/Second_term/PytGA_project")