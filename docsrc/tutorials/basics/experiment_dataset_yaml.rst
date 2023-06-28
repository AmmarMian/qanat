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

* A simple experiment on IRIS dataset that will summary statistics and a PCA plot.
* A simple experiment on MNIST dataset that will summary statistics and a PCA plot.
* An experiment comparing SVM classifiers on IRIS and MNIST datasets.
* An experiment finding the best SVM classifier on IRIS dataset using a grid search.

.. note::
   We rely on python>3.6 and the following packages:
   * numpy
   * pandas
   * matplotlib
   * scikit-learn

   So make sure you have them installed before starting this tutorial. You can install them using pip:

   .. code-block:: console

      pip install numpy pandas matplotlib scikit-learn

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

We can now setup our experiments. Let us first start by doing simple data readers for both datasets. Since it is common code for all experiments, we create a `src` folder in the project root and put a file`data.py` with something like:

.. collapse:: data.py

    .. code:: python

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
                stats[f'hist_{i}'] = np.histogram(features[:, i], bins=10)[0]

            # Correlation matrix
            print('Correlation matrix...')
            stats['corr'] = np.corrcoef(features, rowvar=False)

            # Save the statistics
            with open(os.path.join(args.storage_path, 'stats.pkl'), 'wb') as f:
                pickle.dump(stats, f)
            print(f'Statistics saved in {args.storage_path}')

.. note::
   Notice that we use the `argparse` module to parse the arguments of the script. Especially we parsed `storage_path`, which allows the script ot know where it should store the result, and `dataset_path` which tells the script where to look for the dataset. Those options will be automatically given by Qanat at experiment execution if the project is configured correctly.

TODO: MNIST example


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

    1        summary_iris     Summary statistics on       experiments/summary_sta…    1                        First-order, Histograms,
                              IRIS dataset                                                                      Correlation, Statistics

    2        summary_mnist    Summary statistics on       experiments/summary_sta…    0                        First-order, Histograms,
                              MNIST dataset                                                                     Correlation, Statistics

.. note::
   We can add a --yes option to the command to avoid the confirmation prompt.

.. warning::
   We created the experiments after the datasets. This is important since at the experiment creation we need the name of the datasets that the experiment will use. If we had created the experiments before the datasets, we would have had to edit the experiment description files to add the datasets names.
   We can still add new datasets to an experiment after its creation by using the `qanat experiment update` command.
