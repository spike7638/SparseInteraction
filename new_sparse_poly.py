from sklearn.base import TransformerMixin, BaseEstimator
import numpy as np
import scipy as sp
from scipy.misc import comb
from scipy.sparse import csr_matrix, coo_matrix
from code import interact

"""
For John:

The new mappings don't contain D.
Could you aso do first and second degrees to include the diagonal?


"""

"""
1. Create the feature matrix, include the original matrix in it - the rest will start out all zeros.
2. Iterate with as many nested loops as needed. This is the part that will have a different method for each degree.
"""


"""

(0, 1) = 0
(0, 2) = 1
(1, 2) = 2
(0, 3) = 3

x 0 1 3
x x 2 4
x x x 5
x x x x


we want

0 1 3 6
x 2 4 7
x x 5 8
x x x 9

"""

class SparsePolynomialFeatures(TransformerMixin, BaseEstimator):
    def __init__(self, degree, interaction_only=False, include_bias=False):
    
        if degree > 3:
            raise Exception("SparsePolynomialFeatures currently supports degrees < 4.")
            
        self.degree = degree
        self.interaction_only = interaction_only
        self.include_bias = include_bias
        self.__poly_functs = [] #[self.__second_deg_poly, self.__third_deg_poly]
        self.__inter_functs = [self.__second_deg_inter, self.__third_deg_inter]
    
    def fit(self, X, **fit_params):
        return self
        
    def transform(self, X, Y=None, **transform_params):
    
        X = X.tocoo() #Put back into original format. Also put the new matrix into the same format.
    
        #how big will the output matrix be?
        N, D = X.shape
    
        #start degree at 2 since we're going to just copy the first degree features
        sizes = [int(comb(D, k)) for k in xrange(2, self.degree+1)] if self.interaction_only else [int(comb(D+k-1, D-1)) for k in xrange(2, self.degree+1)]
        print 'the sizes:', sizes
        stop_inds = np.cumsum(sizes)+D #non-inclusive
        offset = D
        
        rows, cols, data = list(X.row), list(X.col), list(X.data) #use linked lists? Contiguous memory might be faster.
        cur_ind = 0
        
        X = X.tocsr()
        
        funct_list = self.__inter_functs if self.interaction_only else self.__poly_functs
        
        for size, stop_ind, degree, funct in zip(sizes, stop_inds, xrange(2, self.degree+1), funct_list):
            print stop_ind, degree, offset            
            funct(X, D, offset, rows, cols, data)
            offset += size
        
        print 'all done'
        interact(local=locals())
        return coo_matrix((data, (rows, cols)), shape=(N, D+sum(sizes))).tocsr()
    
    def __second_deg_inter(self, X, D, offset, rows, cols, data):
        #cur_ind will be used to fill in the correct array elements for when rows, cols, and data are arrays.
        for rownum, row in enumerate(X):
            _, nz_cols = row.nonzero()
            nz_data = row[0, nz_cols].toarray().flatten()
            n_zc = len(nz_data)
            for i in xrange(n_zc):
                col1 = nz_cols[i]
                for j in xrange(i+1, n_zc):
                    col2 = nz_cols[j]
                    output_col = (2*col1 + col2**2 - col2)/2
                    if output_col == (D**2-D)/2+D:
                            print 'This is the culprit2', (i,j)
                    rows.append(rownum)
                    cols.append(output_col + offset)
                    data.append(nz_data[i] * nz_data[j])
    
    def __third_deg_inter(self, X, D, offset, rows, cols, data):
        print 'wow!', offset
        #cur_ind will be used to fill in the correct array elements for when rows, cols, and data are arrays.
        max_out = None
        for rownum, row in enumerate(X):
            _, nz_cols = row.nonzero()
            nz_data = row[0, nz_cols].toarray().flatten()
            n_zc = len(nz_data)
            for i in xrange(n_zc):
                col1 = nz_cols[i]
                part1 = 1 + (col1-1)
                for j in xrange(i+1, n_zc):
                    col2 = nz_cols[j]
                    part2 = part1 + ((col2-1)*col2)/2
                    for k in xrange(j+1, n_zc):
                        col3 = nz_cols[k]
                        output_col = part2 + ((col3-1)**3 + 3*(col3-1)**2 + 2*(col3-1))/6
                        if output_col > max_out:
                            max_out = output_col
                        if output_col > (D**2-D)/2+D:
                            print 'This is the culprit3', (i,j,k)
                        rows.append(rownum)
                        cols.append(output_col + offset)
                        data.append(nz_data[i] * nz_data[j] * nz_data[k])
        print 'max_out', max_out
    
if __name__ == '__main__':
    
    import scipy.sparse
    poly = SparsePolynomialFeatures(3, interaction_only=True)
    X = sp.sparse.random(1, 20, 1).tocsr()
    X_poly = poly.fit_transform(X)
    
    print X_poly
    print X_poly.shape
    print X_poly.nnz