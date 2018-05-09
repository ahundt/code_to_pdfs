
#!/usr/local/bin/python
"""
Combine assignment files into pdfs.

Apache License 2.0 https://www.apache.org/licenses/LICENSE-2.0

"""
import os
import six
import subprocess
from tensorflow.python.platform import flags
from tensorflow.python.platform import gfile
from tensorflow.python.platform import app
import pandas
import grasp_utilities
from PyPDF2 import PdfFileMerger



# progress bars https://github.com/tqdm/tqdm
# import tqdm without enforcing it as a dependency
try:
    from tqdm import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        if args:
            return args[0]
        return kwargs.get('iterable', None)


flags.DEFINE_string(
    'log_dir',
    '~/src/deep-learning-jhu/p03/',
    'Directory for multiple code repositories'
)

flags.DEFINE_string(
    'glob_files',
    'p03*',
    'File path to glob for collecting assignment files in each assignment folder.'
)

flags.DEFINE_string(
    'glob_assignment_folders',
    '*/p03*',
    'File path to glob for collecting individual repository folders.'
)

flags.DEFINE_string(
    'tmp_dir',
    '/tmp/code_to_pdf/',
    'Temporary directory for the file conversion'
)

# flags.DEFINE_string(
#     'sort_by',
#     'val_binary_accuracy',
#     'variable name string to sort results by'
# )

flags.DEFINE_boolean(
    'ascending',
    False,
    'Sort in ascending (1 to 100) or descending (100 to 1) order.'
)

flags.DEFINE_string(
    'save_csv',
    'hyperopt_rank.csv',
    'Where to save the sorted output csv file with the results'
)

flags.DEFINE_string(
    'save_dir',
    './pdfs',
    'Where to save the pdfs, defaults to ./pdfs'
)

flags.DEFINE_boolean(
    'print_results',
    False,
    'Print the results'
)

FLAGS = flags.FLAGS


def mkdir_p(path):
    """Create the specified path on the filesystem like the `mkdir -p` command

    Creates one or more filesystem directory levels as needed,
    and does not return an error if the directory already exists.
    """
    # http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def main(_):
    assignment_folders = gfile.Glob(os.path.join(os.path.expanduser(FLAGS.log_dir), FLAGS.glob_assignment_folders))
    dataframe_list = []
    progress = tqdm(assignment_folders)
    output_files = []
    mkdir_p(FLAGS.tmp_dir)
    for assignment_folder in progress:
        assignment_folder = os.path.expanduser(assignment_folder)
        assignment_folder_basename = os.path.basename(assignment_folder)
        assignment_files = gfile.Glob(os.path.join(assignment_folder, FLAGS.glob_files))
        all_pdfs = []
        for i, assignment_file in enumerate(assignment_files):
            assignment_file_base = os.path.basename(assignment_file)
            if '.py' in assignment_file:
                tex_file = os.path.join(FLAGS.tmp_dir, '{}.tex'.format(assignment_file_base))
                output_pygmentize = subprocess.check_output(
                    ['pygmentize', '-f', 'tex', '-O', 'linenos', '-O', 'title={}.py'.format(assignment_file_base),
                     '-O', 'full', '-O', 'style=default', '-o', tex_file, assignment_file])
                output_pdflatex = subprocess.check_output(
                    ['pdflatex', '-jobname=' + assignment_file_base, '-output-directory=' + FLAGS.tmp_dir, tex_file])
                py_pdf = os.path.join(FLAGS.tmp_dir, tex_file + '.pdf')
                # py files go in back
                all_pdfs += [py_pdf]
            else:
                other_pdf = os.path.join('/tmp', assignment_file_base + '.pdf')
                subprocess.check_output(['pandoc', '-s', assignment_file, '-o', other_pdf])
                # md files go in front
                if '.md' in assignment_file:
                    all_pdfs = [other_pdf] + all_pdfs
                else:
                    # other files go in back
                    all_pdfs += other_pdf


        # https://stackoverflow.com/a/37945454/99379
        merger = PdfFileMerger()

        for pdf in all_pdfs:
            merger.append(pdf)

        output_file = os.path.join(os.path.expanduser(FLAGS.save_dir), assignment_folder_basename + '.pdf')
        merger.write(output_file)
        output_files += [output_file]

            # # progress.write('reading: ' + str(csv_file))
            # try:
            #     dataframe = pandas.read_csv(csv_file, index_col=None, header=0)
            #     # add a filename column for this csv file's name
            #     dataframe['basename'] = os.path.basename(csv_file)
            #     dataframe['csv_filename'] = csv_file
            #     csv_dir = os.path.dirname(csv_file)
            #     hyperparam_filename = gfile.Glob(os.path.join(csv_dir, FLAGS.glob_hyperparams))

            #     # filter specific epochs
            #     if FLAGS.filter_epoch:
            #         dataframe = dataframe.loc[dataframe['epoch'] == FLAGS.epoch]

            #     # manage hyperparams
            #     if len(hyperparam_filename) > 1:
            #         progress.write('Unexpectedly got more than hyperparam file match, '
            #                        'only keeping the first one: ' + str(hyperparam_filename))
            #     hyperparam_filename = hyperparam_filename[0]
            #     dataframe['hyperparameters_filename'] = hyperparam_filename
            #     if FLAGS.load_hyperparams and len(hyperparam_filename) > 0:
            #         hyperparams = grasp_utilities.load_hyperparams_json(hyperparam_filename)
            #         for key, val in six.iteritems(hyperparams):
            #             dataframe[key] = val

            #     # accumulate the data
            #     dataframe_list.append(dataframe)
            # except pandas.io.common.EmptyDataError as exception:
            #     # Ignore empty files, it just means hyperopt got killed early
            #     pass

    # results_df = pandas.DataFrame()
    # results_df = pandas.concat(dataframe_list)
    # results_df = results_df.sort_values(FLAGS.sort_by, ascending=FLAGS.ascending)
    # if FLAGS.print_results:
    #     with pandas.option_context('display.max_rows', None, 'display.max_columns', None):
    #         print(results_df)
    # if FLAGS.save_dir is None:
    #     FLAGS.save_dir = FLAGS.log_dir
    # output_filename = os.path.join(FLAGS.save_dir, FLAGS.save_csv)
    # results_df.to_csv(output_filename)
    print('Processing complete. Results saved to file: ' + str(output_files))

if __name__ == '__main__':
    app.run(main=main)
