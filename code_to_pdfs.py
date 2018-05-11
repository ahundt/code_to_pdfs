
#!/usr/local/bin/python
"""
Combine assignment files into pdfs.

Apache License 2.0 https://www.apache.org/licenses/LICENSE-2.0

"""
import os
import sys
import six
import subprocess
import shutil
from tensorflow.python.platform import flags
from tensorflow.python.platform import gfile
from tensorflow.python.platform import app
# import pandas
from PyPDF2 import PdfFileMerger
import errno
import traceback



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
    'Directory for multiple code repositories, '
    'each of which will be converted to pdf'
)

flags.DEFINE_string(
    'glob_assignment_folders',
    'p03*',
    'File path to glob for collecting individual repository folders.'
    'Can also be a path to a single assignment folder.'
)

flags.DEFINE_string(
    'glob_files',
    'p03*',
    'File path to glob for collecting assignment files in each repository folder.'
)

flags.DEFINE_string(
    'tmp_dir',
    '/tmp/',
    'Temporary directory for the file conversion, '
    'we will create a dir /code_to_pdfs/ in that folder'
    'Warning: files in this location will be deleted!'
)

flags.DEFINE_string(
    'markdown_engines',
    'pandoc,marked',
    'Comma separated list with the order to try different markdown engines.'
    'Options are: pandoc, marked. pandoc seems to do a bit better.'
    'See https://github.com/markedjs/marked and https://pandoc.org/'
    'Pandoc will in turn run many of its own engines if there are problems'
    'so also see the pandoc_markdown_pdf_engines flag for additional settings.'
)

flags.DEFINE_string(
    'pandoc_markdown_pdf_engines',
    'pdflatex,lualatex,wkhtmltopdf,prince',
    'Comma separated list with the order to try pandoc pdf conversion engines.'
    'Options are: pdflatex|lualatex|xelatex|wkhtmltopdf|weasyprint|prince|context|pdfroff.'
    'For details on what these are, see see https://pandoc.org/MANUAL.html'
    'Note that weasyprint is super slow, but it does seem to work ok.'
    'Only relevant while pandoc is one of the markdown_engines flags.'
)

flags.DEFINE_string(
    'pandoc_python_pdf_engines',
    'lualatex,wkhtmltopdf,prince',
    'Comma separated list with the order to try pandoc pdf conversion engines.'
    'Options are: pdflatex|lualatex|xelatex|wkhtmltopdf|weasyprint|prince|context|pdfroff.'
    'Note that weasyprint is super slow, but it does seem to work ok.'
)

flags.DEFINE_string(
    'pandoc_pdf_engines',
    'pdflatex,lualatex,wkhtmltopdf,prince',
    'Comma separated list with the order to try pandoc pdf conversion engines for files except markdown and python.'
    'Options are: pdflatex|lualatex|xelatex|wkhtmltopdf|weasyprint|prince|context|pdfroff.'
    'Note that weasyprint is super slow, but it does seem to work ok.'
)

flags.DEFINE_string(
    'save_dir',
    './pdfs',
    'Where to save the pdfs, defaults to ./pdfs'
)

flags.DEFINE_boolean(
    'verbose',
    True,
    'print extra details for debugging.'
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
    """ Load all the command line arguments and pass them to the primary repository conversion function
    """
    assignment_folders = gfile.Glob(os.path.join(os.path.expanduser(FLAGS.log_dir), FLAGS.glob_assignment_folders))
    dataframe_list = []
    output_files = []
    tmp_dir = os.path.join(FLAGS.tmp_dir, 'code_to_pdfs')
    markdown_engines = FLAGS.markdown_engines.split(',')
    save_dir = FLAGS.save_dir

    # get the list of pdf conversion engines
    pandoc_markdown_pdf_engines = FLAGS.pandoc_markdown_pdf_engines.split(',')
    pandoc_python_pdf_engines = FLAGS.pandoc_python_pdf_engines.split(',')
    pandoc_pdf_engines = FLAGS.pandoc_pdf_engines.split(',')
    glob_files = FLAGS.glob_files
    verbose = FLAGS.verbose

    output_files = repository_to_pdf(
        tmp_dir, assignment_folders, glob_files, pandoc_python_pdf_engines,
        markdown_engines, pandoc_markdown_pdf_engines, save_dir, verbose)

    print('Processing complete generated files: ' + str(output_files))


def repository_to_pdf(
        tmp_dir, assignment_folders, glob_files, pandoc_python_pdf_engines,
        markdown_engines, pandoc_markdown_pdf_engines, save_dir, verbose=False):
    """ Convert one or more repositories to pdf files for grading
    """
    progress = tqdm(assignment_folders)
    html_dir = os.path.join(tmp_dir, 'html')
    # create the temporary working directory
    mkdir_p(tmp_dir)
    # prep the html output directory
    mkdir_p(html_dir)
    output_files = []

    for assignment_folder in progress:
        assignment_folder = os.path.expanduser(assignment_folder)
        assignment_folder_basename = os.path.basename(assignment_folder)
        progress.set_description('Generating: ' + assignment_folder)
        assignment_files = gfile.Glob(os.path.join(assignment_folder, glob_files))

        # clear out the temp directory so we can convert this assignment
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        mkdir_p(tmp_dir)
        mkdir_p(html_dir)
        # generate the pdfs
        all_pdfs = []
        for assignment_file in tqdm(assignment_files):
            assignment_file_base = os.path.basename(assignment_file)

            output_pdf_file = os.path.join(tmp_dir, assignment_file_base + '.pdf')

            pandoc_format = []
            if '.py' in assignment_file[-4:]:

                # turn the code into an html file
                html_file = os.path.join(html_dir, '{}.html'.format(assignment_file_base))
                pandoc_format = ['-f', 'html']

                # pandoc format param is same as pygments format command for html
                # http://pygments.org/docs/cmdline/
                pygment_command = ['pygmentize'] + pandoc_format
                pygment_command += ['-O', 'full,style=colorful', '-O', 'linenos',
                                    '-O', 'title={}'.format(assignment_file_base),
                                    '-o', html_file, assignment_file]
                run_command_line(pygment_command, write=progress, cwd=assignment_folder)
                pdf_engine_order = pandoc_python_pdf_engines

                # use google chrome to render the html version of the python file to pdf
                # https://developers.google.com/web/updates/2017/04/headless-chrome
                # https://www.npmjs.com/package/chrome-headless-render-pdf
                pdf_success = chrome_html_to_pdf(html_file, output_pdf_file, progress, assignment_folder)

            elif '.md' in assignment_file[-4:]:
                pdf_success = markdown_to_pdf(
                    html_dir, assignment_file, progress, assignment_folder,
                    output_pdf_file, markdown_engines, pandoc_markdown_pdf_engines)
            else:
                progress.write('WARNING: Skipping file: ' + assignment_file)
                # skip this one, it is probably a backup or something
                continue

            if pdf_success:
                # md files go in front, other files go in back
                if '.md' in assignment_file:
                    all_pdfs = [output_pdf_file] + all_pdfs
                else:
                    # other files go in back
                    all_pdfs += [output_pdf_file]
            else:
                progress.write('WARNING: FAILED TO CONVERT ' + output_pdf_file)

        output_file = os.path.join(os.path.expanduser(save_dir), assignment_folder_basename + '.pdf')
        if verbose:
            progress.write('Generating pdf: ' + output_file + ' from folder: ' + assignment_folder + ' by combining: ' + str(all_pdfs))

        mkdir_p(save_dir)
        merge_pdfs(all_pdfs, output_file)
        output_files += [output_file]

        if verbose:
            progress.write('PDF Complete: ' + str(output_file))
    return output_files


def merge_pdfs(all_pdfs, output_file):
    """ Merge a bunch of separately created pdf files into one and write to disk.
    """
    # Merge all the individually created pdf files
    # https://stackoverflow.com/a/37945454/99379
    merger = PdfFileMerger()

    for pdf in all_pdfs:
        merger.append(pdf)

    merger.write(output_file)


def markdown_to_pdf(html_dir, input_file, write, cwd, output_pdf_file, markdown_engines, pandoc_markdown_pdf_engines):
    """ Convert a markdown file to pdf

        output_pdf_file: the pdf file path to output.
        cwd: current working directory, the directory the command would be run from if it was run on the command line.
        markdown_engines: see markdown_engines flag in this file.
        pandoc_markdown_pdf_engines: see pandoc_markdown_pdf_engines flag in this file.
    """
    pdf_success = False
    input_file_base = os.path.basename(input_file)
    for engine in markdown_engines:
        try:
            if engine == 'marked':
                html_file = os.path.join(html_dir, '{}.html'.format(input_file_base))
                # https://github.com/markedjs/marked
                marked_html_command = ['marked', '-i', input_file, '-o', html_file]
                run_command_line(marked_html_command, write=write, cwd=cwd)
                # use google chrome to render the html version of the python file to pdf
                # https://developers.google.com/web/updates/2017/04/headless-chrome
                # https://www.npmjs.com/package/chrome-headless-render-pdf
                pdf_success = chrome_html_to_pdf(html_file, output_pdf_file, write, cwd)
            elif engine == 'pandoc':
                pandoc_format = ['-f', 'gfm']
                pdf_engine_order = pandoc_markdown_pdf_engines
                pdf_success = pandoc_convert_to_pdf(input_file, output_pdf_file, cwd, pandoc_format, pdf_engine_order, write)
            else:
                raise ValueError('Unsupported markdown renderer ' + str(engine))

        except subprocess.CalledProcessError as ex:
            # try another one
            m1 = 'Error Converting with ' + engine + ' engine: \n'
            ex_type, ex, tb = sys.exc_info()
            # apparently subprocess.CalledProcessError doesn't have a traceback
            # m2 = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
            m2 = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=tb))
            message = m1 + m2
            write.write(message)
            # deletion must be explicit to prevent leaks
            # https://stackoverflow.com/a/16946886/99379
            del tb
    return pdf_success


def chrome_html_to_pdf(html_file, output_pdf_file, progress, cwd):
    # use google chrome to render the html version of the python file to pdf
    # https://developers.google.com/web/updates/2017/04/headless-chrome
    # https://www.npmjs.com/package/chrome-headless-render-pdf
    chrome_render_command = ['chrome-headless-render-pdf', '--url', 'file://' + html_file,
                             '--pdf', output_pdf_file]
    run_command_line(chrome_render_command, write=progress, cwd=cwd)
    pdf_success = True
    return pdf_success

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


def pandoc_convert_to_pdf(input_file, pdf_output_file, cwd, pandoc_format, pdf_engine_order=None, write=sys.stdout):
    """
    pandoc format: ['-f', 'html']
    """
    pdf_success = False
    if pdf_engine_order is None:
        pdf_engine_order = FLAGS.pdf_engine_order
    # walk through trying the pdf engine order for this file
    for engine in pdf_engine_order:
        try:
            # Try converting the file with the various available pdf engines
            # until one of them succeeds
            # see https://pandoc.org/MANUAL.html
            # gfm is github flavored markdown
            pandoc_command = ['pandoc', '-s', input_file, '-o', pdf_output_file,
                              '--resource-path', cwd, '--pdf-engine={}'.format(engine)]
            pandoc_command += pandoc_format
            run_command_line(pandoc_command, write=write, cwd=cwd)
            pdf_success = True
            break
        except subprocess.CalledProcessError as ex:
            # try another one
            m1 = 'Error Converting with ' + engine + ' engine: \n'
            ex_type, ex, tb = sys.exc_info()
            # apparently subprocess.CalledProcessError doesn't have a traceback
            # m2 = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
            m2 = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=tb))
            message = m1 + m2
            write.write(message)
            # deletion must be explicit to prevent leaks
            # https://stackoverflow.com/a/16946886/99379
            del tb
    return pdf_success


def run_command_line(command, write=sys.stdout, **kwargs):
    """ Run a command line command with subprocess.check_output()

    Also adds a little extra debug printout options.
    """
    if FLAGS.verbose and write is not None:
        command_for_printing = ' '.join(command)
        write.write('>>> ' + command_for_printing)
    output_pygmentize = subprocess.check_output(command, **kwargs)
    return output_pygmentize

if __name__ == '__main__':
    app.run(main=main)
