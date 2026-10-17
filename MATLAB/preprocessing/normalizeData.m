function [x_norm, normParams] = normalizeData(x, x_min, x_max)
% NORMALIZEDATA Reusable min-max normalization for FPGA-friendly preprocessing.
%
% Formula:
%   x_norm = (x - x_min) / (x_max - x_min)
%
% Features:
%   - Explicitly handles x_max == x_min (returns zeros without division by zero)
%   - Clips values to [0, 1] if values exceed specified bounds
%   - If x_min and x_max are not provided, computes min(x) and max(x)
%
% Inputs:
%   x     - Numerical array or scalar to normalize
%   x_min - (Optional) Lower bound
%   x_max - (Optional) Upper bound
%
% Outputs:
%   x_norm     - Normalized array with values bounded in [0.0, 1.0]
%   normParams - struct with fields 'min', 'max', 'range'

    if nargin < 1 || isempty(x)
        error('normalizeData:EmptyInput', 'Input data array x cannot be empty.');
    end
    if ~isnumeric(x) || any(isnan(x(:))) || any(isinf(x(:)))
        error('normalizeData:InvalidData', 'Input data must be finite numbers.');
    end

    if nargin < 2 || isempty(x_min)
        x_min = min(x(:));
    end
    if nargin < 3 || isempty(x_max)
        x_max = max(x(:));
    end

    if x_min > x_max
        error('normalizeData:InvalidBounds', 'x_min (%f) cannot exceed x_max (%f).', x_min, x_max);
    end

    rangeVal = x_max - x_min;

    if rangeVal <= eps
        % Avoid division by zero when max == min
        x_norm = zeros(size(x));
    else
        x_norm = (x - x_min) ./ rangeVal;
        % Ensure exact [0, 1] bounds
        x_norm = max(0.0, min(1.0, x_norm));
    end

    normParams = struct( ...
        'min', double(x_min), ...
        'max', double(x_max), ...
        'range', double(rangeVal));
end
