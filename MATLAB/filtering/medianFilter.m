function y = medianFilter(x, N)
% MEDIANFILTER High-precision reference implementation of Sliding Median Filter.
%
% Properties:
%   - Golden reference model with double-precision floating-point arithmetic.
%   - Rejects isolated impulsive outliers and sensor spikes without phase lag.
%   - Windows are centered or truncated at edges.
%
% Inputs:
%   x - Input signal (scalar or 1D array)
%   N - Window size (positive odd integer >= 1, default = 3)
%
% Output:
%   y - Filtered signal with identical dimensions as x

    if nargin < 1 || isempty(x)
        error('medianFilter:EmptyInput', 'Input signal x cannot be empty.');
    end
    if ~isnumeric(x) || any(isnan(x(:))) || any(isinf(x(:)))
        error('medianFilter:InvalidData', 'Signal contains non-numeric, NaN, or Inf values.');
    end

    if nargin < 2 || isempty(N)
        N = 3;
    else
        N = double(N);
    end

    if N < 1 || floor(N) ~= N
        error('medianFilter:InvalidWindowSize', 'Window size N must be an integer >= 1.');
    end

    len = length(x);
    y = zeros(size(x));
    halfWin = floor(N / 2);

    for k = 1:len
        wStart = max(1, k - halfWin);
        wEnd = min(len, k + halfWin);
        window = x(wStart:wEnd);
        y(k) = median(window);
    end
end
