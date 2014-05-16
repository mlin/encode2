#!/usr/bin/env python
# chip_seq_2 0.0.1
# Generated by dx-app-wizard.
#
# Basic execution pattern: Your app will run on a single machine from
# beginning to end.
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import os
import dxpy

ENCODE_CHIP_SEQ_PROJECT = 'project-BJ7Kj200p2zX7qjB1j8001YK'

REPLICATES_FOLDER = '/replicates'
CONTROLS_FOLDER = '/controls'
PSEUDO_REPLICATES_FOLDER = '/pseudo_replicates'
SPP_FOLDER = '/spp'
IDR_FOLDER = '/idr'

def find_reference_file_by_name(reference_name):
    '''Looks up a reference file by name in the project that holds common tools. From Joe Dale's code.'''

    found = dxpy.find_one_data_object(classname="file", name=reference_name,
                                      project=ENCODE_CHIP_SEQ_PROJECT,
                                      folder='/Reference Data',
                                      recurse=True,
                                      zero_ok=False, more_ok=False, return_handler=True)
    print "Resolved %s to %s" % (reference_name, found.get_id())
    return dxpy.dxlink(found)

def find_applet_by_name(applet_name):
    '''Looks up an applet by name in the project that holds tools.  From Joe Dale's code.'''

    found = dxpy.find_one_data_object(classname="applet", name=applet_name,
                                      project=ENCODE_CHIP_SEQ_PROJECT,
                                      zero_ok=False, more_ok=False, return_handler=True)
    print "Resolved %s to %s" % (applet_name, found.get_id())
    return found

@dxpy.entry_point('main')
def main(**job_inputs):
    '''This function will populate the workflow for the ChIP-Seq Pipeline.'''
    # First, sort, filter, and remove duplicates if asked.
    project_name = dxpy.describe(dxpy.PROJECT_CONTEXT_ID)['name']
    if job_inputs['sort_filter_and_remove_dups']:
        job_inputs['duplicates_removed'] = True
        sorted_replicates = []
        applet = find_applet_by_name('sort_and_filter_bams')
        for replicate in job_inputs['replicates']:
            sort_replicates_input = {'input_bam': replicate}
            job = applet.run(sort_replicates_input, folder=REPLICATES_FOLDER)
            sorted_replicates += [job.get_output_ref('output_bam')]
        replicates = sorted_replicates

        sorted_controls = []
        for control in job_inputs['controls']:
            sort_controls_input = {'input_bam': control}
            job = applet.run(sort_controls_input, folder=CONTROLS_FOLDER)
            sorted_controls += [job.get_output_ref('output_bam')]
        controls = sorted_controls

    if job_inputs['duplicates_removed']:
        spp_app_name = 'spp_nodups'
    else:
        spp_app_name = 'spp'

    # Now, check to see if we need to merge the controls into a larger control.
    applet = find_applet_by_name('merge_bams')
    if len(controls) > 1:
        control_merge_input = {'input_bams': controls}
        job = applet.run(control_merge_input, folder=CONTROLS_FOLDER)
        control_merge_output = job.get_output_ref('merged_bam')
    else:
        control_merge_output = controls[0]

    replicate_merge_input = {'input_bams': replicates}
    job = applet.run(replicate_merge_input, folder=REPLICATES_FOLDER)
    replicate_merge_output = job.get_output_ref('merged_bam')

    applet = find_applet_by_name(spp_app_name)
    pooled_replicate_v_control_spp_input = {'input_bam': replicate_merge_output, 'control_bam': control_merge_output}
    job = applet.run(pooled_replicate_v_control_spp_input, folder=SPP_FOLDER)
    pooled_replicate_v_control_peaks = job.get_output_ref('peaks')

    applet = find_applet_by_name('pseudoreplicator')
    pooled_pseudo_replicate_input = {'input_bam': replicate_merge_output}
    job = applet.run(pooled_pseudo_replicate_input, folder=REPLICATES_FOLDER)
    pooled_pseudo_replicate_1 = job.get_output_ref('pseudoreplicate_bam1')
    pooled_pseudo_replicate_2 = job.get_output_ref('pseudoreplicate_bam2')

    applet = find_applet_by_name(spp_app_name)
    pooled_pseudo_replicate_1_v_control_spp_input = {'input_bam': pooled_pseudo_replicate_1, 'control_bam': control_merge_output}
    job = applet.run(pooled_pseudo_replicate_1_v_control_spp_input, folder=SPP_FOLDER)
    pooled_pseudo_replicate_peaks = [job.get_output_ref('peaks')]

    pooled_pseudo_replicate_2_v_control_spp_input = {'input_bam': pooled_pseudo_replicate_2, 'control_bam': control_merge_output}
    job = applet.run(pooled_pseudo_replicate_2_v_control_spp_input, folder=SPP_FOLDER)
    pooled_pseudo_replicate_peaks += [job.get_output_ref('peaks')]

    replicates_v_controls_peaks = []
    pseudo_replicates_v_controls_peaks = []
    for replicate in replicates:
        pseudo_replicator_input = {'input_bam': replicate}
        applet = find_applet_by_name('pseudoreplicator')
        job = applet.run(pseudo_replicator_input, folder=PSEUDO_REPLICATES_FOLDER)
        pseudo_replicate_1 = job.get_output_ref('pseudoreplicate_bam1')
        pseudo_replicate_2 = job.get_output_ref('pseudoreplicate_bam2')

        applet = find_applet_by_name(spp_app_name)
        replicate_v_control_spp_input = {'input_bam': replicate, 'control_bam': control_merge_output}
        job = applet.run(replicate_v_control_spp_input, folder=SPP_FOLDER)
        replicates_v_controls_peaks += [job.get_output_ref('peaks')]

        pseudo_replicate_1_v_control_spp_input = {'input_bam': pseudo_replicate_1, 'control_bam': control_merge_output}
        job = applet.run(pseudo_replicate_1_v_control_spp_input, folder=SPP_FOLDER)
        pseudo_replicates_v_controls_peaks += [job.get_output_ref('peaks')]

        pseudo_replicate_2_v_control_spp_input = {'input_bam': pseudo_replicate_2, 'control_bam': control_merge_output}
        job = applet.run(pseudo_replicate_2_v_control_spp_input, folder=SPP_FOLDER)
        pseudo_replicates_v_controls_peaks += [job.get_output_ref('peaks')]

    idr_input = {'replicate_peaks_files': replicates_v_controls_peaks,
                 'pseudo_replicate_peaks_files': pseudo_replicates_v_controls_peaks,
                 'pooled_replicate_peaks_file': pooled_replicate_v_control_peaks,
                 'pooled_pseudo_replicate_peaks_file': pooled_pseudo_replicate_peaks,
                 'replicate_peaks_threshold': 0.01,
                 'pseudo_replicate_peaks_threshold': 0.02,
                 'pooled_pseudo_replicate_peaks_threshold': 0.0025,
                 'output_prefix': project_name,
                 'ranking_measure': 'signal.value',
                 'genome_table_filename': 'genome_table.human.hg19.txt'}
    applet = find_applet_by_name('idr')
    job = applet.run(idr_input, folder=IDR_FOLDER)

    output = {}

    return output

dxpy.run()