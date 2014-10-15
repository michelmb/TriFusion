#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  
#  Copyright 2012 Unknown <diogo@arch>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  Author: Diogo N. Silva
#  Version: 0.1
#  Last update: 11/02/14

from collections import OrderedDict


class Cluster():
	""" Object for clusters of the OrthoMCL groups file. It is useful to set a number of attributes that will make
	subsequent filtration and processing much easier """

	def __init__(self, line_string):
		"""
		To initialize a Cluster object, only a string compliant with the format of a cluster in an OrthoMCL groups
		file has to be provided. This line should contain the name of the group, a colon, and the sequences belonging
		to that group separated by whitespace
		:param line_string: String of a cluster
		"""

		# Initializing attributes for parse_string
		self.name = None
		self.sequences = None
		self.species_frequency = {}

		# Initializing attributes for apply filter
		self.gene_compliant = None  # If the value is different than None, this will inform downstream objects of
		# whether this cluster is compliant with the specified gene_threshold
		self.species_compliant = None  # If the value is different than None, this will inform downstream objects of
		# whether this cluster is compliant with the specified species_threshold

		self.parse_string(line_string)

	def parse_string(self, cluster_string):
		"""
		Parses the string and sets the group name and sequence list attributes
		"""

		fields = cluster_string.split(":")
		# Setting the name and sequence list of the clusters
		self.name = fields[0].strip()
		self.sequences = fields[1].strip().split()

		# Setting the gene frequency for each species in the cluster
		species_list = set([field.split("|")[1] for field in self.sequences])
		self.species_frequency = dict((species, frequency) for species, frequency in zip(species_list,
										map(lambda species: str(self.sequences).count(species), species_list)))

	def apply_filter(self, gene_threshold, species_threshold):
		"""
		This method will update two Cluster attributes, self.gene_flag and self.species_flag, which will inform
		downstream objects if this cluster respects the gene and species threshold
		:param gene_threshold: Integer for the maximum number of gene copies per species
		:param species_threshold: Integer for the minimum number of species present
		"""

		# Check whether cluster is compliant with species_threshold
		if len(self.species_frequency) >= species_threshold:
			self.species_compliant = True
		else:
			self.species_compliant = False

		# Check whether cluster is compliant with gene_threshold
		if max(self.species_frequency.values()) <= gene_threshold:
			self.gene_compliant = True
		else:
			self.gene_compliant = False


class Group ():
	""" This represents the main object of the orthomcl toolbox module. It is initialized with a file name of a
	orthomcl groups file and provides several methods that act on that group file. To process multiple Group objects,
	see MultiGroups object """

	def __init__(self, groups_file, gene_threshold=None, species_threshold=None, project_prefix="MyGroups"):

		# Initializing thresholds. These may be set from the start, or using some method that uses them as arguments
		self.gene_threshold = gene_threshold
		self.species_threshold = species_threshold

		# Initialize the project prefix for possible ouput files
		self.prefix = project_prefix
		# Initialize attributes for the parser_groups method
		self.groups = []
		self.name = None
		# Parse groups file and populate groups attribute
		self.__parse_groups(groups_file)

	def __parse_groups(self, groups_file):
		"""
		Parses the ortholog clusters in the groups file and populates the self.groups ordered dictionary containing the
		group number as key and the sequence references as values in list mode.
		For each group, it also creates a dictionary containing the gene frequency of each species. This dictionary
		is added as the second elements of the group's dictionary value.
		A final self.groups dictionary should be like: {groups1: [[seq_spA, seq_spB, seq_spC], {spA:1, spB:1, spC:1}]}
		:param groups_file: File name for the orthomcl groups file
		:return: populates the groups attribute
		"""

		self.name = groups_file
		groups_file_handle = open(groups_file)

		for line in groups_file_handle:
			cluster_object = Cluster(line)

			if self.species_threshold is not None and self.gene_threshold is not None:
				cluster_object.apply_filter(self.gene_threshold, self.species_threshold)
				self.groups.append(cluster_object)

	def basic_group_statistics(self):
		"""
		This method creates a basic table in list format containing basic information of the groups file (total
		number of clusters, total number of sequences, number of clusters below the gene threshold, number of
		clusters below the species threshold and number of clusters below the gene AND species threshold)
		:return: List containing number of [total clusters, total sequences, clusters above gene threshold,
		clusters above species threshold, clusters above gene and species threshold]
		"""
		# Total number of clusters
		total_cluster_num = len(self.groups)

		# Remaining counters
		total_sequence_num = 0
		clusters_gene_threshold = 0
		clusters_species_threshold = 0
		clusters_all_threshold = 0

		for cluster in self.groups:
			# For total number of sequences
			sequence_num = len(cluster.sequences)
			total_sequence_num += sequence_num

			# For clusters above species threshold
			if cluster.species_compliant is True:
				clusters_species_threshold += 1

			# For clusters below gene threshold
			if cluster.gene_compliant is True:
				clusters_gene_threshold += 1

			if cluster.species_compliant is True and cluster.gene_compliant is True:
				clusters_all_threshold += 1

		statistics = [total_cluster_num, total_sequence_num, clusters_species_threshold, clusters_gene_threshold,
					 clusters_all_threshold]

		return statistics

	def export_filtered_group(self, output_file_name="filtered_groups"):
		""" Writes the filtered groups into a new file """

		output_handle = open(output_file_name, "w")

		for cluster in self.groups:
			if cluster.species_compliant is True and cluster.gene_compliant is True:
				output_handle.write("%s: %s\n" % (cluster.name, " ".join(cluster.sequences)))

		output_handle.close()


class MultiGroups ():
	""" Creates an object composed of multiple Group objects """

	def __init__(self, groups_files, gene_threshold=None, species_threshold=None, project_prefix="MyGroups"):
		"""
		:param groups_files: A list containing the file names of the multiple group files
		:return: Populates the self.multiple_groups attribute
		"""

		# Initializing thresholds. These may be set from the start, or using some method that uses them as arguments
		self.gene_threshold = gene_threshold
		self.species_threshold = species_threshold

		self.prefix = project_prefix

		self.multiple_groups = []

		for group_file in groups_files:

			group_object = Group(group_file, self.gene_threshold, self.species_threshold)
			self.multiple_groups.append(group_object)

	def basic_multigroup_statistics(self, output_file_name="multigroup_base_statistics.csv"):
		"""
		:param output_file_name:
		:return:
		"""

		# Creates the storage for the statistics of the several files
		statistics_storage = OrderedDict()

		for group in self.multiple_groups:
			group_statistics = group.basic_group_statistics()
			statistics_storage[group.name] = group_statistics

		output_handle = open(self.prefix + "." + output_file_name, "w")
		output_handle.write("Group file; Total clusters; Total sequences; Clusters below gene threshold; Clusters "
							"above species threshold; Clusters below gene and above species thresholds\n")

		for group, vals in statistics_storage.items():
			output_handle.write("%s; %s\n" % (group, ";".join([str(x) for x in vals])))

		output_handle.close()