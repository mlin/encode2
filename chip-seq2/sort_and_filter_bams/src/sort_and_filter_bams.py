#!/usr/bin/env python
# merge_bams 0.0.1
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
import subprocess
import multiprocessing
import re

import dxpy

def get_java_cmd():
    # Calc amount of memory available for gatk and Picard.
    total_mem = re.findall('^MemTotal:[\s]*([0-9]*) kB',
                           open('/proc/meminfo').read())
    if(len(total_mem) != 1):
        raise dxpy.DXError('Problem reading system memory from /proc/meminfo')
    mem = int(0.9 * int(total_mem[0]) / 1024.0)
    java_cmd = 'java -Xmx{mem}m '.format(mem=mem)

    return java_cmd

def sort_bam(job_inputs):
    input_bam = dxpy.DXFile(job_inputs['input_bam'])
    fn = input_bam.describe()['name']
    dxpy.download_dxfile(input_bam.get_id(), fn)

    sorted_ofn = os.path.splitext(fn)[0] + '_sorted.bam'
    cmd = '/sambamba sort -t {0} -o /dev/stdout {1} '.format(multiprocessing.cpu_count()-1, fn)
    if job_inputs['quality_filter']:
        cmd += '| /sambamba view -f bam -F "(mapping_quality > 1) and not unmapped" -o /dev/stdout /dev/stdin '
    cmd += '> ' + sorted_ofn
    print cmd
    subprocess.check_call(cmd, shell=True)

    if job_inputs['remove_duplicates']:
        deduped_ofn = os.path.splitext(sorted_ofn)[0] + '_deduped.bam'
        md_metrics_ofn = os.path.splitext(sorted_ofn)[0] + '_deduped_metrics.txt'
        cmd = get_java_cmd()
        cmd += ' -jar /MarkDuplicates.jar I={0} O={1} METRICS_FILE={2} ASSUME_SORTED=true VALIDATION_STRINGENCY=LENIENT REMOVE_DUPLICATES=true '.format(sorted_ofn, deduped_ofn, md_metrics_ofn)
        print cmd
        subprocess.check_call(cmd, shell=True)
        bam_file = dxpy.dxlink(dxpy.upload_local_file(deduped_ofn).get_id())
        metrics_file = dxpy.dxlink(dxpy.upload_local_file(md_metrics_ofn).get_id())
    else:
        bam_file = dxpy.dxlink(dxpy.upload_local_file(sorted_ofn).get_id())
        metrics_file = None

    return {'bam_file': bam_file, 'metrics_file': metrics_file}

@dxpy.entry_point('main')
def main(input_bam, quality_filter=True, remove_duplicates=True):
    sort_inputs = {'input_bam': input_bam, 'quality_filter': quality_filter, 'remove_duplicates': remove_duplicates}
    sort_output = sort_bam(sort_inputs)

    output = {'output_bam': sort_output['bam_file'],
              'dedup_metrics_file': sort_output['metrics_file']}

    return output

dxpy.run()