from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from mpmath import mpf


HMMParams = namedtuple(
    'Params',
    ['transition_prob', 'emission_prob', 'initial_prob']
)


def forward(hmm, X, Y, Yt):
    n = len(Yt)
    m = len(X)
    alpha = np.asmatrix(np.zeros((n, m), dtype=mpf))

    alpha[0, :] = (
        hmm.initial_prob *
        np.diag(hmm.emission_prob[:, Yt[0]].A1)
    )
    #alpha[0, :] /= np.sum(alpha[0, :])

    for t in xrange(1, n):
        alpha[t, :] = (
            alpha[t - 1, :] *
            hmm.transition_prob *
            np.asmatrix(np.diag(hmm.emission_prob[:, Yt[t]].A1))
        )
        #alpha[t, :] /= np.sum(alpha[t, :])

    return np.asmatrix(alpha)


def backward(hmm, X, Y, Yt):
    n = len(Yt)
    m = len(X)
    beta = np.asmatrix(np.zeros((n, m), dtype=mpf))

    beta[n - 1, :] = [mpf(1.0)] * m

    for t in xrange(n - 2, -1, -1):
        beta[t, :] = (
            hmm.transition_prob *
            np.asmatrix(np.diag(hmm.emission_prob[:, Yt[t + 1]].A1)) *
            beta[t + 1, :].T
        ).T
        #beta[t, :] /= np.sum(beta[t, :])

    return np.asmatrix(beta)


def baum_welch(hmm, X, Y, Yt, iterations=1):
    # TODO: change this so that it checks the difference between
    # current and previous run rather than running for a fixed number
    # of iterations.
    iteration = 0
    while iteration < iterations:
        iteration += 1

        n = len(Yt)
        m = len(X)
        Yt = [Y.index(yt) for yt in Yt]

        alpha = forward(hmm, X, Y, Yt)
        beta = backward(hmm, X, Y, Yt)

        gamma = np.asmatrix(np.zeros((n, m), dtype=mpf))
        for t in xrange(n):
            gamma[t, :] = [alpha[t, i] * beta[t, i] for i in xrange(m)]
            gamma[t, :] /= np.sum(gamma[t, :])

        xsi = np.zeros((n, m, m), dtype=mpf)
        for t in xrange(n - 1):
            den = mpf(0.0)
            for i in xrange(m):
                for j in xrange(m):
                    xsi[t, i, j] = (
                        alpha[t, i] *
                        hmm.transition_prob[i, j] *
                        beta[t + 1, j] *
                        hmm.emission_prob[j, Yt[t + 1]]
                    )
            xsi[t] /= np.sum(xsi[t])

        # Update
        pi = gamma[0]

        transition_prob = np.asmatrix(np.zeros((m, m), dtype=mpf))
        for i in xrange(m):
            den = np.sum(gamma[:, i])
            for j in xrange(m):
                transition_prob[i, j] = np.sum(xsi[:, i, j]) / den

        emission_prob = np.asmatrix(np.zeros((m, len(Y)), dtype=mpf))
        for i in xrange(m):
            den = np.sum(gamma[:, i])
            for j in xrange(len(Y)):
                emission_prob[i, j] = np.sum(gamma[np.array(Yt) == j, i]) / den

        hmm = HMMParams(transition_prob, emission_prob, pi)

    return hmm


def forward_backward(hmm_params, X, Y, sequence):
    n = len(sequence)
    m = len(X)
    seq_indices = [Y.index(yt) for yt in sequence]
    alpha = forward(hmm_params, X, Y, seq_indices)
    beta = backward(hmm_params, X, Y, seq_indices)
    prob = np.zeros((n, m), dtype=mpf)
    for t in xrange(n):
        for i in xrange(m):
            prob[t, i] = alpha[t, i] * beta[t, i]
    return prob

# A = np.matrix([[0.5, 0.5], [0.3, 0.7]])
# B = np.matrix([[0.3, 0.7], [0.8, 0.2]])
# pi = np.array([0.2, 0.8])

#if __name__ == '__main__':
transition_prob = np.matrix([
    map(mpf, [0.0, 1.0, 0.0, 0.0]),
    map(mpf, [0.0, 1 - 0.0002, 0.0002, 0.0]),
    map(mpf, [0.0, 0.0, 1 - 0.0002, 0.0002]),
    map(mpf, [0.0, 0.0, 0.0, 0.0]),
], dtype=mpf)

emission_prob = np.matrix([
    map(mpf, [1.0, 0.0, 0.0, 0.0, 0.0]),
    map(mpf, [0.0, 0.96, 0.036, 0.004, 0.0]),
    map(mpf, [0.0, 0.96, 0.004, 0.036, 0.0]),
    map(mpf, [0.0, 0.0, 0.0, 0.0, 1.0]),
], dtype=mpf)

initial_prob = np.matrix(
    map(mpf, [1.0, 0.0, 0.0, 0.0]),
    dtype=mpf,
)

HIDDEN_STATES = ['S0', 'S1', 'S2', 'S3']
SYMBOLS = ['S', 'N', 'L', 'R', 'E']

with open('seq2.txt') as fp:
    sequences = [line.strip() for line in fp.readlines()]

for i, seq in enumerate(sequences[:1]):
    #print 'Sekwencja %d: %s' % (i, seq)
    hmm_params = baum_welch(
        HMMParams(
            transition_prob=transition_prob,
            emission_prob=emission_prob,
            initial_prob=initial_prob,
        ),
        HIDDEN_STATES,
        SYMBOLS,
        seq)
    print hmm_params
    prob = forward_backward(hmm_params, HIDDEN_STATES, SYMBOLS, seq)
    print prob

    matplotlib.rc('xtick', labelsize=5)
    plt.xticks(range(0, len(seq)), seq)
    plt.plot(prob[0:len(seq), 1:3])
    plt.show()
