Experiments, Datasets and description files
============================================
.. sectnum::
  :start: 2

.. note::
   In this tutorial, we will see the notion of dataset and its linking to experiments. We will also see how to describe experiments and datasets using a YAML description file rather than from a prompt.

.. note::
   The code of this tutorial is available at: TODO


Objectives
----------

In this tutorial we will use the classic IRIS and MNIST datasets to illustrate the notion of dataset and experiment. We will produce the following experiments:

* A simple experiment on IRIS dataset that will compute summary statistics and a PCA plot.
* A simple experiment on MNIST dataset that will compute summary statistics and a PCA plot.

.. note::
   We rely on python>3.6 and the following packages:
   * numpy
   * pandas
   * matplotlib
   * seaborn

   So make sure you have them installed before starting this tutorial. You can install them using pip:

   .. code-block:: console

      pip install numpy pandas matplotlib seaborn

   We also assume python executable is called with alias `python`.

Setting up the project and environment
--------------------------------------


Let us create a new directory and initialize a new Qanat project:

.. code-block:: console

   mkdir iris_mnist
   cd iris_mnist
   qanat init . --yes

.. note::
   The `--yes` option is used to avoid the interactive prompt. It is useful for scripting.

Let us also download both IRIS and MNIST datasets:

.. code-block:: console

   mkdir data; cd data
   wget https://archive.ics.uci.edu/static/public/53/iris.zip
   unzip iris.zip -d iris
   rm iris.zip

   mkdir mnist; cd mnist
   wget http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz
   wget http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz
   wget http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz
   wget http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz
   gzip -d train-images-idx3-ubyte.gz
   gzip -d train-labels-idx1-ubyte.gz
   gzip -d t10k-images-idx3-ubyte.gz
   gzip -d t10k-labels-idx1-ubyte.gz
   cd ../..

.. warning::
   The links provided above may change. If so, please update the links accordingly.
   They were working at the writing of this tutorial: 2023-06-28.

We can now setup our experiments. Let us first start by doing simple data readers for both datasets. Since it is common code for all experiments, we create a `src` folder in the project root and put a file `data.py` with something like:

.. collapse:: data.py

    .. code:: python

        import pandas as pd
        import numpy as np
        import os


        def load_iris(path):
            """Load the IRIS dataset.

            Parameters
            ----------
            path: str
                Path to the dataset.

            Returns
            -------
            X: np.ndarray
                Features.
            y: np.ndarray
                Labels (0, 1, 2).
            z: list
                List of class names.
            """
            # If path is a directory, we assume that the dataset is in the directory
            if os.path.isdir(path):
                _path = os.path.join(path, 'iris.data')
            else:
                _path = path

            df = pd.read_csv(_path, header=None)
            X = df.iloc[:, :-1].values
            y = df.iloc[:, -1].values
            z = df.iloc[:, -1].unique().tolist()
            y = np.array([z.index(i) for i in y])

            return X, y, z


        def load_mnist(path, kind='train'):
            """Load the MNIST dataset.

            Parameters
            ----------
            path: str
                Path to the dataset.

            kind: str
                'train' or 'test'.

            Returns
            -------
            X: np.ndarray
                Features.
            y: np.ndarray
                Labels (0, 1, 2).
            """

            if kind == 'train':
                _path = os.path.join(path, 'train-images-idx3-ubyte')
                X = _load_mnist_images(_path)
                _path = os.path.join(path, 'train-labels-idx1-ubyte')
                y = _load_mnist_labels(_path)
            elif kind == 'test':
                _path = os.path.join(path, 't10k-images-idx3-ubyte')
                X = _load_mnist_images(_path)
                _path = os.path.join(path, 't10k-labels-idx1-ubyte')
                y = _load_mnist_labels(_path)
            else:
                raise ValueError('kind must be either train or test')

            return X, y


        def _load_mnist_images(path):
            """Load the MNIST images.

            Parameters
            ----------
            path: str

            Returns
            -------
            X: np.ndarray
            """
            with open(path, 'rb') as f:
                magic = int.from_bytes(f.read(4), 'big')
                n = int.from_bytes(f.read(4), 'big')
                rows = int.from_bytes(f.read(4), 'big')
                cols = int.from_bytes(f.read(4), 'big')
                X = np.fromfile(f, dtype=np.uint8)
            return X.reshape(n, rows, cols)


        def _load_mnist_labels(path):
            """Load the MNIST labels.

            Parameters
            ----------
            path: str

            Returns
            -------
            y: np.ndarray
            """
            with open(path, 'rb') as f:
                magic, n = np.fromfile(f, dtype=np.int32, count=2)
                y = np.fromfile(f, dtype=np.uint8)
            return y

We also add a `__init__.py` file in the `src` folder to make it a python package.

Setting up IRIS experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^

We can now setup our first experiment. Let us create a folder `summary_statistics` in the `experiments` folder. In this folder, we create a `iris.py` file that will perform some computation of statistics for the IRIS dataset. It will have something like:

.. collapse:: iris.py

    .. code:: python

        import numpy as np
        import argparse
        import pickle
        import os
        from importlib.machinery import SourceFileLoader

        # Import the dataset loader by computing relative path
        loader_path = os.path.join(
                os.path.dirname(__file__), '../..', 'src', 'data.py')
        loader = SourceFileLoader('data', loader_path).load_module()


        if __name__ == "__main__":

            parser = argparse.ArgumentParser(description='Iris dataset statistics')
            parser.add_argument('--storage_path', type=str, required=True,
                                help='Path to the storage directory of'
                                'the computed statistics')
            parser.add_argument('--dataset_path', type=str, required=True,
                                help='Path to the iris dataset')
            args = parser.parse_args()

            # Load the dataset
            features, labels, classes = loader.load_iris(args.dataset_path)

            # Compute the statistics
            print('Computing statistics...')
            stats = {}

            # Basic statistics
            print('Basic statistics...')
            stats['nb_samples'] = features.shape[0]
            stats['nb_features'] = features.shape[1]
            stats['nb_classes'] = len(classes)
            stats['classes'] = classes
            stats['mean'] = np.mean(features, axis=0)
            stats['std'] = np.std(features, axis=0)
            stats['min'] = np.min(features, axis=0)
            stats['max'] = np.max(features, axis=0)
            stats['median'] = np.median(features, axis=0)

            # Histograms
            print('Histograms...')
            for i in range(features.shape[1]):
                stats[f'hist_{i}'] = np.histogram(features[:, i], bins=10)

            # Correlation matrix
            print('Correlation matrix...')
            stats['corr'] = np.corrcoef(features, rowvar=False)

            # PCA
            print('PCA...')
            cov = np.cov(features, rowvar=False)
            eig_vals, eig_vecs = np.linalg.eig(cov)
            idx = eig_vals.argsort()[::-1]
            eig_vals = eig_vals[idx]
            eig_vecs = eig_vecs[:, idx]

            # Compute the projection of the data on the first two principal components
            proj = np.dot(features, eig_vecs[:, :2])

            stats['pca'] = {'eig_vals': eig_vals, 'eig_vecs': eig_vecs, 'proj': proj}

            # Data also stored since it is not too big
            stats['features'] = features
            stats['labels'] = labels

            # Save the statistics
            with open(os.path.join(args.storage_path, 'stats.pkl'), 'wb') as f:
                pickle.dump(stats, f)
            print(f'Statistics saved in {args.storage_path}')

.. note::
   Notice that we use the `argparse` module to parse the arguments of the script. Especially we parsed `storage_path`, which allows the script ot know where it should store the result, and `dataset_path` which tells the script where to look for the dataset. Those options will be automatically given by Qanat at experiment execution if the project is configured correctly.

.. note::
   Since we placed `src` package in the root of the project, we need to tell python where to find it. This is done by adding the following lines at the beginning of the script:

    .. code:: python

         import os
         from importlib.machinery import SourceFileLoader

         # Import the dataset loader by computing relative path
         loader_path = os.path.join(
                os.path.dirname(__file__), '../..', 'src', 'data.py')
         loader = SourceFileLoader('data', loader_path).load_module()

    Another way to do this is to add the root of the project to the `PYTHONPATH` environment variable, but this is not recommended as it can lead to conflicts with other projects. You can also add it temporarily with `sys.path.append`.

    This is not necessary if the `src` package is in the same folder as the experiment script, but since we want to share the `src` package between experiments, we put it in the root of the project.

While we are at it, let us create a `plot_iris.py` in the same folder to plot the IRIS dataset as an Action. It will have something like:

.. collapse:: plot_iris.py

    .. code:: python

        import numpy as np
        import matplotlib.pyplot as plt
        import pickle
        import os
        import seaborn as sns
        import argparse

        sns.set(style="darkgrid")

        # Setup LaTeX for plotting if available
        try:
            plt.rc('text', usetex=True)
            plt.rc('font', family='serif')
        except:
            pass

        if __name__ == "__main__":

            parser = argparse.ArgumentParser(
                    description='Plot summary statistics of the iris dataset')
            parser.add_argument('--storage_path', type=str, required=True,
                                help='Path to the precomputed summary statistics')
            args = parser.parse_args()

            # Load the data
            with open(os.path.join(args.storage_path, 'stats.pkl'), 'rb') as f:
                stats = pickle.load(f)

            # Plot first order stats as bar plots
            mean = stats['mean']
            std = stats['std']
            min_ = stats['min']
            max_ = stats['max']
            median = stats['median']
            classes = stats['classes']
            nb_classes = stats['nb_classes']
            nb_features = stats['nb_features']
            nb_samples = stats['nb_samples']
            feature_names = ['sepal length', 'sepal width',
                             'petal length', 'petal width']

            # First : mean, std, min, max, median, horizontal bar plot
            fig, ax = plt.subplots(1, 5, figsize=(17, 3))
            for i, kind in enumerate(['mean', 'std', 'min', 'max', 'median']):
                if i == 0:
                    ax[i].barh(np.arange(nb_features), stats[kind],
                               tick_label=feature_names)
                else:
                    ax[i].barh(np.arange(nb_features), stats[kind])
                    ax[i].set_yticklabels([])
                    ax[i].set_yticks([])
                ax[i].set_title(kind)

            # Same info as above but in a box plot for each feature
            fig = plt.figure(figsize=(6,4))
            for i in range(nb_features):
                plt.boxplot(stats['features'][:, i], positions=[i],
                            showmeans=True,
                            meanline=True, meanprops={'color': 'red'},
                            medianprops={'color': 'blue'},
                            boxprops={'color': 'black'},
                            whiskerprops={'color': 'black'},
                            capprops={'color': 'black'})
            plt.xticks(np.arange(nb_features), feature_names)
            plt.title('Box plot of the features')

            # Plot the histogram of each feature sotred in
            # stats['hist_i' % feature_no]
            fig, ax = plt.subplots(2, 2, figsize=(10, 8))
            for i in range(nb_features):
                hist, bins = stats[f'hist_{i}']
                center = (bins[:-1] + bins[1:]) / 2
                ax[i//2, i % 2].bar(center, hist, width=0.1)
                ax[i//2, i % 2].set_title(f'Histogram of {feature_names[i]}')
            plt.tight_layout()

            # Plot the correlation matrix
            fig = plt.figure(figsize=(8, 4))
            sns.heatmap(stats['corr'], annot=True, cmap='coolwarm')
            plt.xticks(np.arange(nb_features)+0.5, feature_names)
            plt.yticks(np.arange(nb_features)+0.5, feature_names,
                       rotation=0, va='center')
            plt.title('Correlation matrix')

            # Plot the PCA: scatter plot of the first two components
            # with color indicating the class and eigenvectors as arrows
            # indicating the direction of the variance
            fig = plt.figure(figsize=(10, 6))
            eig_vals, eig_vecs = stats['pca']['eig_vals'], stats['pca']['eig_vecs']
            proj = stats['pca']['proj']

            plt.scatter(proj[:, 0], proj[:, 1], c=stats['labels'], cmap='viridis')

            # Plot the eigenvectors
            colors = ['r', 'b']
            mean = np.mean(proj, axis=0)
            for i in range(2):
                plt.arrow(mean[0], mean[1],
                          eig_vals[i]*eig_vecs[i, 0],
                          eig_vals[i]*eig_vecs[i, 1],
                          head_width=0.1, head_length=0.1,
                          fc=colors[i], ec=colors[i])

            plt.title('PCA: first two components')
            plt.xlabel('First component')
            plt.ylabel('Second component')

            # Plot eigenvalues
            fig = plt.figure(figsize=(8, 4))
            plt.scatter(np.arange(nb_features), eig_vals)
            plt.xlabel('Eigenvalue index')
            plt.ylabel('Eigenvalue')
            plt.title('Eigenvalues of the covariance matrix')

            plt.show()

Setting up the MNIST experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For MNIST, we can do something similar in the same folder `experiments/summary_statistics` with a `mnist.py` file:

.. collapse:: mnist.py

   .. code:: python

        import numpy as np
        import argparse
        import pickle
        import os
        from importlib.machinery import SourceFileLoader

        # Import the dataset loader by computing relative path
        loader_path = os.path.join(
                os.path.dirname(__file__), '../..', 'src', 'data.py')
        loader = SourceFileLoader('data', loader_path).load_module()


        if __name__ == "__main__":

            parser = argparse.ArgumentParser(description='MNIST dataset statistics')
            parser.add_argument('--storage_path', type=str, required=True,
                                help='Path to the storage directory of'
                                'the computed statistics')
            parser.add_argument('--dataset_path', type=str, required=True,
                                help='Path to the iris dataset')
            args = parser.parse_args()

            # Load the dataset: train and test sets
            X_train, y_train = loader.load_mnist(args.dataset_path, 'train')
            X_test, y_test = loader.load_mnist(args.dataset_path, 'test')

            # Compute the statistics
            print('Computing statistics...')
            stats = {}
            stats['train'] = {}
            stats['test'] = {}

            # Basic statistics
            print('Basic statistics...')
            for kind, X, y in zip(['train', 'test'], [X_train, X_test],
                                [y_train, y_test]):
                stats[kind]['n_samples'] = X.shape[0]
                stats[kind]['n_features'] = X.shape[1] * X.shape[2]
                stats[kind]['n_classes'] = len(np.unique(y))
                stats[kind]['n_samples_per_class'] = np.bincount(y)

            # Correlation matrix
            print('Correlation matrix...')
            for kind, X in zip(['train', 'test'], [X_train, X_test]):
                X = X.reshape(X.shape[0], -1)
                stats[kind]['correlation'] = np.corrcoef(X, rowvar=False)

            # PCA
            print('PCA...')
            for kind, X in zip(['train', 'test'], [X_train, X_test]):
                X = X.reshape(X.shape[0], -1)
                cov = np.cov(X, rowvar=False)
                eigvals, eigvecs = np.linalg.eig(cov)
                stats[kind]['pca'] = {}
                stats[kind]['pca']['eigvals'] = eigvals
                stats[kind]['pca']['eigvecs'] = eigvecs

            # Save the statistics
            with open(os.path.join(args.storage_path, 'stats.pkl'), 'wb') as f:
                pickle.dump(stats, f)
            print(f'Statistics saved in {args.storage_path}')

.. note::
   The `plot_mnist.py` is let as an exercise to the reader.

Project structure
^^^^^^^^^^^^^^^^^

At this point the project structure should look like this:

.. code:: console

    ❯ tree .
    .
    ├── data
    │   ├── iris
    │   │   ├── bezdekIris.data
    │   │   ├── Index
    │   │   ├── iris.data
    │   │   └── iris.names
    │   ├── iris.yaml
    │   ├── mnist
    │   │   ├── t10k-images-idx3-ubyte
    │   │   ├── t10k-labels-idx1-ubyte
    │   │   ├── train-images-idx3-ubyte
    │   │   └── train-labels-idx1-ubyte
    │   └── mnist.yaml
    ├── experiments
    │   └── summary_statistics
    │       ├── iris.py
    │       ├── mnist.py
    │       ├── plot_iris.py
    │       └── plot_mnist.py
    ├── results
    └── src
        ├── data.py
        └── __init__.py

    7 directories, 18 files

Adding datsets to the project
-----------------------------

Since we are using datasets, let us formalize this in our project by telling Qanat about them. To do that we can use the command `qanat dataset new` which shows a prompt that allows to tell Qanat what are the names, description, path and tags of the dataset. We can also use a YAML description file. Let us create two files in `data`:

* `iris.yaml`:

.. code:: yaml

    name: iris
    description: Iris dataset
    path: data/iris
    tags: [csv, iris, classification]

* `mnist.yaml`:

.. code:: yaml

    name: mnist
    description: MNIST dataset
    path: data/mnist
    tags: [mnist, classification, images]

We can now add those datasets to our project by running:

.. code:: console

    qanat dataset new data/iris.yaml
    qanat dataset new data/mnist.yaml

We can check that the datasets have been added by running:

.. code:: console

    qanat dataset list

which should output something like:

.. code:: console

    Total number of datasets: 2
    ID      Name        Description         Path                                               Tags
    🆔 2    🔖 iris     💬 Iris dataset     📁 data/iris         🏷  csv, 🏷  iris, 🏷  classification
    🆔 3    🔖 mnist    💬 MNIST dataset    📁 data/mnist    🏷  mnist, 🏷  classification, 🏷  images

.. note::
   We can add a --yes option to the command to avoid the confirmation prompt.

Adding a new experiment thanks to a description file
------------------------------------------------------

We can now add a new experiment to our project. To that end rather than using the prompt, we can setup a YAML description file. Let us create a folder `experiments_details` in our project root and the file `summary_statistics_iris.yaml` with the following content:

.. code:: yaml

    name: summary_iris
    description: Summary statistics on IRIS dataset
    path: experiments/summary_statistics
    executable: experiments/summary_statistics/iris.py
    executable_command: python
    datasets:
      - iris
    tags:
      - First-order
      - Histograms
      - Correlation
      - Statistics
    actions:
      - plot:
          name: plot
          executable: experiments/summary_statistics/plot_iris.py
          executable_command: python
          description: Plot summary statistics about the dataset

and the file `summary_statistics_mnist.yaml` with the following content:

.. code:: yaml

    name: summary_mnist
    description: Summary statistics on MNIST dataset
    path: experiments/summary_statistics
    executable: experiments/summary_statistics/mnist.py
    executable_command: python
    datasets:
      - mnist
    tags:
      - First-order
      - Histograms
      - Correlation
      - Statistics
    actions:
      - plot:
          name: plot
          executable: experiments/summary_statistics/plot_mnist.py
          executable_command: python
          description: Plot summary statistics about the dataset

We can now add those experiments to our project by running:

.. code:: console

    qanat experiment new -f experiments_details/summary_statistics_iris.yaml
    qanat experiment new -f experiments_details/summary_statistics_mnist.yaml

We can check that the experiments have been added by running:

.. code:: console

    qanat experiment list

which should output something like:

.. code:: console

   🆔 ID    🔖 Name          💬 Description              📁 Path                     ⏳ Number of runs                         🏷  Tags

    1        summary_iris     Summary statistics on       experiments/summary_sta…    0                        First-order, Histograms,
                              IRIS dataset                                                                      Correlation, Statistics

    2        summary_mnist    Summary statistics on       experiments/summary_sta…    0                        First-order, Histograms,
                              MNIST dataset                                                                     Correlation, Statistics

.. note::
   We can add a --yes option to the command to avoid the confirmation prompt.

.. warning::
   We created the experiments after the datasets. This is important since at the experiment creation we need the name of the datasets that the experiment will use. If we had created the experiments before the datasets, we would have had to edit the experiment description files to add the datasets names.
   We can still add new datasets to an experiment after its creation by using the `qanat experiment update` command.

Running the experiments
-----------------------

Now that everything is setup for the two first experiments, we can run them. To that end we can use the `qanat experiment run` command:

.. code:: console

    qanat experiment run summary_iris
    qanat experiment run summary_mnist

This will run the experiments and store the results in the `results` folder. The first command will have the following output (minus the occasional git commit step):

.. code:: console

    [10:51:06] INFO     Run 1 created.                                                                                      run.py:1078
               INFO     Setting up the run...                                                                               run.py:1179
               INFO     Single group of parameters detected                                                                 runs.py:209
               INFO     Creating                                                                                            runs.py:210
                        /home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/results/summa
                        ry_iris/run_1
               INFO     Running the experiment...                                                                           run.py:1188
               INFO     Launching the execution of the run                                                                  runs.py:429
               INFO     Running 1 executions sequentially                                                                   runs.py:545
               INFO     The output of the executions will be redirected to                                                  runs.py:547
                        /home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/results/summa
                        ry_iris/run_1
               INFO     Running 'python experiments/summary_statistics/iris.py --storage_path                               runs.py:568
                        /home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/results/summa
                        ry_iris/run_1 --dataset_path
                        /home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/data/iris'
               WARNING  Do not close the terminal window. It will cancel the execution of the run.                          runs.py:569
               INFO     Finished ['python', 'experiments/summary_statistics/iris.py', '--storage_path',                     runs.py:606
                        '/home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/results/summ
                        ary_iris/run_1', '--dataset_path',
                        '/home/ammarmian/programming_projects/qanat-examples/qanat-tutorials/basics/iris_mnist/data/iris']

      Running.. ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
               INFO     Updating database with finished time

As you can notice, the actual running command has the two options `--storage_path` and `--dataset_path` automatically filled by Qanat.

.. note::
   If multiple datasets are used by the experiment, the `--dataset_path` option will be repeated for each dataset.

After executing the two commands, we can check that the results have been stored in the `results` folder by running:

.. code:: console

    ❯ tree results
    results/
    ├── summary_iris
    │   └── run_1
    │       ├── group_info.yaml
    │       ├── info.yaml
    │       ├── stats.pkl
    │       ├── stderr.txt
    │       └── stdout.txt
    └── summary_mnist
        └── run_2
            ├── group_info.yaml
            ├── info.yaml
            ├── stats.pkl
            ├── stderr.txt
            └── stdout.txt

    4 directories, 10 files

We can also check that the database has been updated by running:

.. code:: console

   ❯ qanat experiment status summary_iris
    🔖 Name: summary_iris
    💬 Description: Summary statistics on IRIS dataset
    📁 Path: experiments/summary_statistics
    💾 Datasets:['iris']
    ⚙ Executable: experiments/summary_statistics/iris.py
    ⚙ Execute command: python
    ⏳ Number of runs: 1
    🏷  Tags: ['First-order', 'Histograms', 'Correlation', 'Statistics']
    🛠 Actions:
      - plot: Plot summary statistics about the dataset

    ⏳ Runs:
    🆔 ID    💬 Description    📁 Path             🖥 Runner    📆 Launch date     ⏱ Duration        🔍 Status    🏷  Tags    ⏳ Progress
    1                          results/summary…     local      2023-06-29         0:00:00.319506       🏁
                                                               10:51:06.260540

To show the plots of the `summary_iris` experiment, we can run:

.. code:: console

   ❯ qanat experiment action summary_iris plot 1
   [10:56:17] INFO     Executing action 'plot' on run 1 of experiment summary_iris                                       actions.py:94
              INFO     Action command: python experiments/summary_statistics/plot_iris.py --storage_path                actions.py:114
                       results/summary_iris/run_1

Conclusion
----------

In this tutorial we have seen how to create a project, add datasets and experiments to it, and run the experiments using a YAML description file. In the next tutorial, we will see how to run these experiments as a job on a cluster with a job-submission system.
