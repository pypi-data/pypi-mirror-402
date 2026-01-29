import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from math import sqrt, log
from scipy.optimize import minimize
import random

def dimension_calculation(dataframe: pd.DataFrame, method: str = "nearest-neighbour-3") -> int:
    if dataframe.empty:
        raise ValueError("Dataframe must not be empty.")

    if dataframe.shape[1] < 2:
        raise ValueError("Dataframe must contain at least two columns.")

    METHODS = ["variance-ratio", "n1", "n2", "infinite-n", "MCMC", "nearest-neighbour-1", "nearest-neighbour-2", "nearest-neighbour-3"]
    if method not in METHODS:
        raise ValueError(f'Unknown method: "{method}".\nAvailable methods are: "{'" ; "'.join(METHODS)}".')

    # Replace NaN values with 0
    dataframe.fillna(0, inplace=True)

    # List of columns containing text
    text_columns = dataframe.select_dtypes(include=["object"]).columns

    # Replacing text with numerical values
    for column in text_columns:
        le = LabelEncoder()
        dataframe[column] = le.fit_transform(dataframe[column].astype(str))

    # Creating a MinMaxScaler object
    scaler = MinMaxScaler()

    # Normalisation of DataFrame columns
    dataframe = pd.DataFrame(scaler.fit_transform(dataframe), columns=dataframe.columns)

    if method == "variance-ratio":
        # Calculate the covariance matrix
        cov_matrix = np.cov(dataframe, rowvar=False)

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Calculate the sum of eigenvalues
        total_variance = np.sum(eigenvalues)

        # Calculate the proportions of variance
        variance_ratios = eigenvalues / total_variance

        # Calculate the number of effective dimensions
        effective_dimensions = np.sum(variance_ratios > 0.01)

        # Return the number of effective dimensions
        return effective_dimensions

    if method == "n1":
        # Calculate the covariance matrix
        cov_matrix = np.cov(dataframe, rowvar=False)

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Calculation of the sum of eigenvalues
        sum_eigenvalues = np.sum(eigenvalues)

        result = 1
        for eigenvalue in eigenvalues:
            if eigenvalue < 0 or sum_eigenvalues <= 0:
                # Skip this iteration if the values are invalid
                continue
            result *= (eigenvalue / sum_eigenvalues) ** (-eigenvalue / sum_eigenvalues)

        if not np.isnan(result) and not np.isinf(result):
            return round(result)
        else:
            raise ValueError("Invalid result.")

    if method == "n2":
        # Calculate the covariance matrix
        cov_matrix = np.cov(dataframe, rowvar=False)

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Calculation of the sum of eigenvalues
        sum_eigenvalues = np.sum(eigenvalues)

        # Calculation of the sum of squared eigenvalues
        sum_eigenvalues_square = np.sum(eigenvalues**2)

        # Calculate the number of effective dimensions
        effective_dimensions = (sum_eigenvalues**2) / sum_eigenvalues_square

        # Return the number of effective dimensions
        return round(effective_dimensions)

    if method == "infinite-n":
        # Calculate the covariance matrix
        cov_matrix = np.cov(dataframe, rowvar=False)

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        # Calculation of the sum of eigenvalues
        sum_eigenvalues = np.sum(eigenvalues)

        # Calculate the number of effective dimensions
        effective_dimensions = sum_eigenvalues / max(eigenvalues)

        # Return the number of effective dimensions
        return round(effective_dimensions)

    if method == "MCMC":
        pca = PCA(n_components = min(dataframe.shape[1], 50))
        X_pca = pca.fit_transform(dataframe)

        # Define the parameters of the Markov chain
        num_samples = 1000
        num_features = X_pca.shape[1]

        # Initialise the Markov chain
        chain = np.zeros((num_samples, num_features))

        # Generate the Markov chain
        for i in range(1, num_samples):
            # Sampling a new normal distribution proposal
            proposal = np.random.multivariate_normal(chain[i-1], np.eye(num_features))

            # Calculate the probability densities of the current and proposed proposals
            current_density = np.exp(-np.sum((chain[i-1] - X_pca)**2) / 2)
            proposal_density = np.exp(-np.sum((proposal - X_pca)**2) / 2)

            # Accept or reject the proposal using the Metropolis-Hastings criterion
            acceptance_ratio = min(1, proposal_density / current_density)
            if np.random.rand() < acceptance_ratio:
                chain[i] = proposal
            else:
                chain[i] = chain[i-1]

        # Calculate the number of effective dimensions from a Markov chain
        cov_matrix = np.cov(chain.T)
        _, eigenvalues, _ = np.linalg.svd(cov_matrix)
        cumulative_variance = np.cumsum(eigenvalues) / np.sum(eigenvalues)
        effective_dimensions = np.sum(cumulative_variance < 0.99) + 1

        # Return the number of effective dimensions from a Markov chain
        return effective_dimensions

    if method == "nearest-neighbour-1":
        def euclidean_distance(point_p, point_q):
            # Calculation of the sum of the squares of the differences
            sum_of_squares = sum(((q - p) ** 2) for p, q in zip(point_p, point_q))
            # Calculation of Euclidean distance
            distance = sqrt(sum_of_squares)
            return distance

        def hl(n, L):
            return (1/C) * ((log(n)/n)**(1/L))

        def Un(n, L):
            random_rows = dataframe.sample(n)
            h = hl(n, L)
            sum = 0
            d = 0
            for k in range(0, n-1, 2):
                a = (1/(h**L)) * abs(1 - ((euclidean_distance(random_rows.iloc[k], [0 for i in range(D)]))**2)/(h*h))
                b = (1/(h**L)) * abs(1 - ((euclidean_distance(random_rows.iloc[k+1], random_rows.iloc[k]))**2)/(h*h))
                c = (1/(h**L)) * abs(1 - ((euclidean_distance(random_rows.iloc[k+1], [0 for i in range(D)]))**2)/(h*h))
                sum = sum + (a+b+c) / 3
                d = d + 1
            return sum / d

        def absolute_slope_least_squares(x, y, weights):
            # Definition of the error function to be minimised
            def error_function(params):
                m = params[0]
                c = params[1]
                absolute_errors = np.abs(y - (m * x + c))
                weighted_errors = weights * absolute_errors
                return np.sum(weighted_errors)
            # Initialising settings
            initial_params = np.array([0.0, 0.0])
            # Minimisation of the error function
            result = minimize(error_function, initial_params)
            # Recovery of optimal settings
            m_opt = result.x[0]
            c_opt = result.x[1]
            return m_opt, c_opt

        X = dataframe.values

        # Calculating distances using the k nearest neighbours
        k_values = range(2, 31)
        distances = []

        for k in k_values:
            nbrs = NearestNeighbors(n_neighbors=k, metric="euclidean").fit(X)
            distances_k, _ = nbrs.kneighbors(X)
            min_distance_k = np.min(distances_k[:, -1])
            distances.append(min_distance_k)

        C = np.mean(distances)
        N = dataframe.shape[0]
        D = dataframe.shape[1]

        S = []
        for l in range(1, 20):
            X = []
            Y = []
            for k in range(1, 6):
                X.append(np.log(hl(N//k, l)))
                Y.append(np.log(Un(N//k, l)))
            weights = np.array([1, 1/2, 1/3, 1/4, 1/5])
            slope = abs(absolute_slope_least_squares(np.array(X), np.array(Y), weights)[0])
            S.append(slope)

        # Calculate the number of effective dimensions
        minimum = min(S)
        effective_dimensions = S.index(minimum) + 1

        # Return the number of effective dimensions
        return effective_dimensions

    if method == "nearest-neighbour-2":
        def Tj_x(distances, j):
            return distances[j]

        k = 30
        nbrs = NearestNeighbors(n_neighbors=k+1, metric="euclidean").fit(dataframe.values)
        distances, _ = nbrs.kneighbors(dataframe.values)

        sum = 0
        random_indices = random.sample(range(dataframe.shape[0]), 500)
        for i in random_indices:
            mk_x = 0
            for j in range(1, k):
                a = np.log(Tj_x(distances[i], k) / Tj_x(distances[i], j))
                mk_x += a
            mk_x = (1 / (k-1) * mk_x) ** (-1)
            sum += (mk_x ** (-1))

        # Calculate the number of effective dimensions
        effective_dimensions = round(((1 / 500) * sum) ** (-1))

        # Return the number of effective dimensions
        return effective_dimensions

    if method == "nearest-neighbour-3":
        def split_dataframe(dataframe):
            dataframe_1 = pd.DataFrame()
            dataframe_2 = pd.DataFrame()
            for column in dataframe.columns:
                unique_values = dataframe[column].nunique()
                if unique_values <= 2:
                    dataframe_1[column] = dataframe[column]
                else:
                    dataframe_2[column] = dataframe[column]
            return dataframe_1, dataframe_2

        binary_df, non_binary_df = split_dataframe(dataframe)

        if binary_df.empty:
            effective_dimensions_1 = 0
        elif binary_df.shape[1] == 1:
            effective_dimensions_1 = 1
        else:
            # Calculate the covariance matrix
            cov_matrix = np.cov(binary_df, rowvar=False)

            # Eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

            # Calculate the sum of eigenvalues
            total_variance = np.sum(eigenvalues)

            # Calculate the proportions of variance
            variance_ratios = eigenvalues / total_variance

            # Calculate the number of effective dimensions
            effective_dimensions_1 = np.sum(variance_ratios > 0.01)

        def Tj_x(distances, j):
            return distances[j]

        if non_binary_df.empty:
            effective_dimensions_2 = 0
        else:
            k = 30
            nbrs = NearestNeighbors(n_neighbors=k+1, metric='euclidean').fit(non_binary_df.values)
            distances, _ = nbrs.kneighbors(non_binary_df.values)

            sum = 0
            random_indices = random.sample(range(non_binary_df.shape[0]), 500)
            for i in random_indices:
                mk_x = 0
                for j in range(1, k):
                    a = np.log(Tj_x(distances[i], k) / Tj_x(distances[i], j))
                    mk_x += a
                mk_x = (1 / (k-1) * mk_x) ** (-1)
                sum += (mk_x ** (-1))

            effective_dimensions_2 = round(((1 / 500) * sum) ** (-1))

        # Calculate the number of effective dimensions
        effective_dimensions = round(effective_dimensions_1 * (binary_df.shape[1] / dataframe.shape[1]) + effective_dimensions_2 * (non_binary_df.shape[1] / dataframe.shape[1]))

        # Return the number of effective dimensions
        return effective_dimensions