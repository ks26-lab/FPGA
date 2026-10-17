function y = movingAverage(x, N)
% MOVINGAVERAGE High-precision reference implementation of Causal Moving Average.
%
% Formula:
%   y[k] = (1 / N) * sum_{i=0}^{N-1} x[k-i]
%
% Properties:
%   - Golden reference model with double-precision floating-point arithmetic.
%   - Handles single samples or full time-series vectors.
%   - Causal window matching FPGA shift-register accumulator pipeline.
%
% Inputs:
%   x - Input signal (scalar or 1D array)
%   N - Window size (positive integer >= 1, default = 4)
%
% Output:
%   y - Filtered signal with identical dimensions as x

    if nargin < 1 || isempty(x)
        error('movingAverage:EmptyInput', 'Input signal x cannot be empty.');
    end
    if ~isnumeric(x) || any(isnan(x(:))) || any(isinf(x(:)))
        error('movingAverage:InvalidData', 'Signal contains non-numeric, NaN, or Inf values.');
    end

    if nargin < 2 || isempty(N)
        N = 4;
    else
        N = double(N);
    end

    if N < 1 || floor(N) ~= N
        error('movingAverage:InvalidWindowSize', 'Window size N must be an integer >= 1.');
    end

    len = length(x);
    y = zeros(size(x));

    for k = 1:len
        startIdx = max(1, k - N + 1);
        window = x(startIdx:k);
        y(k) = sum(window) / length(window);
    end
end
