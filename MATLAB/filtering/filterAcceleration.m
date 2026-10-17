function res = filterAcceleration(acceleration, method, param)
% FILTERACCELERATION Filters acceleration sensor signal.
%
% Inputs:
%   acceleration - Raw acceleration in m/s^2 [-50, 50] (scalar or vector)
%   method       - (Optional) 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param        - (Optional) Filter parameter (alpha or window size)
%
% Outputs:
%   res          - struct containing:
%                    .rawAcceleration
%                    .filteredAcceleration
%                    .filteringMethod
%                    .filterParameter
%                    .accelerationChange
%                    .validityStatus
%                    .units

    if nargin < 1 || isempty(acceleration)
        error('filterAcceleration:EmptyInput', 'Acceleration signal cannot be empty.');
    end
    if ~isnumeric(acceleration) || any(isnan(acceleration(:))) || any(isinf(acceleration(:)))
        error('filterAcceleration:InvalidSignal', 'Acceleration contains non-numeric, NaN, or Inf values.');
    end
    if any(abs(acceleration) > 50)
        error('filterAcceleration:OutOfRange', 'Acceleration magnitude must be within [-50, 50] m/s^2.');
    end

    if nargin < 2, method = "EMA"; end
    if nargin < 3, param = []; end

    [filteredAccel, methodUsed, paramUsed] = applyFilterKernel(acceleration, method, param);

    if length(filteredAccel) > 1
        accelChange = filteredAccel(end) - filteredAccel(1);
    else
        accelChange = 0.0;
    end

    res = struct( ...
        'rawAcceleration', acceleration, ...
        'filteredAcceleration', filteredAccel, ...
        'filteringMethod', string(methodUsed), ...
        'filterParameter', paramUsed, ...
        'accelerationChange', accelChange, ...
        'validityStatus', true, ...
        'units', "m/s^2");
end
