function res = filterVelocity(velocity, method, param)
% FILTERVELOCITY Filters vehicle / body velocity sensor signal.
%
% Inputs:
%   velocity - Raw velocity in m/s [-100, 100] (scalar or vector)
%   method   - (Optional) 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param    - (Optional) Filter parameter (alpha or window size)
%
% Outputs:
%   res      - struct containing:
%                .rawVelocity
%                .filteredVelocity
%                .filteringMethod
%                .filterParameter
%                .velocityChange
%                .validityStatus
%                .units

    if nargin < 1 || isempty(velocity)
        error('filterVelocity:EmptyInput', 'Velocity signal cannot be empty.');
    end
    if ~isnumeric(velocity) || any(isnan(velocity(:))) || any(isinf(velocity(:)))
        error('filterVelocity:InvalidSignal', 'Velocity contains non-numeric, NaN, or Inf values.');
    end
    if any(abs(velocity) > 100)
        error('filterVelocity:OutOfRange', 'Velocity magnitude must be within [-100, 100] m/s.');
    end

    if nargin < 2, method = "EMA"; end
    if nargin < 3, param = []; end

    [filteredVel, methodUsed, paramUsed] = applyFilterKernel(velocity, method, param);

    if length(filteredVel) > 1
        velocityChange = filteredVel(end) - filteredVel(1);
    else
        velocityChange = 0.0;
    end

    res = struct( ...
        'rawVelocity', velocity, ...
        'filteredVelocity', filteredVel, ...
        'filteringMethod', string(methodUsed), ...
        'filterParameter', paramUsed, ...
        'velocityChange', velocityChange, ...
        'validityStatus', true, ...
        'units', "m/s");
end
