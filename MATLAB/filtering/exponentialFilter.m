function y = exponentialFilter(x, alpha, y0)
% EXPONENTIALFILTER High-precision reference implementation of Exponential Moving Average (EMA).
%
% Formula:
%   y[k] = alpha * x[k] + (1 - alpha) * y[k-1]
%
% Properties:
%   - Golden reference model with double-precision floating-point arithmetic.
%   - Matches FPGA DSP multiply-accumulate structure.
%   - Initial condition y[1] = x[1] (or y0 if explicitly provided).
%
% Inputs:
%   x     - Input signal (scalar or 1D array)
%   alpha - Smoothing factor (0 < alpha <= 1, default = 0.25)
%   y0    - (Optional) Initial filter state
%
% Output:
%   y     - Filtered signal with identical dimensions as x

    if nargin < 1 || isempty(x)
        error('exponentialFilter:EmptyInput', 'Input signal x cannot be empty.');
    end
    if ~isnumeric(x) || any(isnan(x(:))) || any(isinf(x(:)))
        error('exponentialFilter:InvalidData', 'Signal contains non-numeric, NaN, or Inf values.');
    end

    if nargin < 2 || isempty(alpha)
        alpha = 0.25;
    else
        alpha = double(alpha);
    end

    if alpha <= 0 || alpha > 1
        error('exponentialFilter:InvalidAlpha', 'Smoothing parameter alpha must satisfy 0 < alpha <= 1.');
    end

    len = length(x);
    y = zeros(size(x));

    if nargin >= 3 && ~isempty(y0)
        y_prev = double(y0);
    else
        y_prev = x(1);
    end

    y(1) = alpha * x(1) + (1.0 - alpha) * y_prev;
    for k = 2:len
        y(k) = alpha * x(k) + (1.0 - alpha) * y(k - 1);
    end
end
