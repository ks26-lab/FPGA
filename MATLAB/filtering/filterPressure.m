function res = filterPressure(pressure, method, param)
% FILTERPRESSURE Filters hydrostatic / ambient pressure sensor signal.
%
% Inputs:
%   pressure - Raw pressure in kPa [0, 150000] (scalar or vector)
%   method   - (Optional) 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param    - (Optional) Filter parameter (alpha or window size)
%
% Outputs:
%   res      - struct containing:
%                .rawPressure
%                .filteredPressure
%                .filteringMethod
%                .filterParameter
%                .pressureChange
%                .validityStatus
%                .units

    if nargin < 1 || isempty(pressure)
        error('filterPressure:EmptyInput', 'Pressure signal cannot be empty.');
    end
    if ~isnumeric(pressure) || any(isnan(pressure(:))) || any(isinf(pressure(:)))
        error('filterPressure:InvalidSignal', 'Pressure contains non-numeric, NaN, or Inf values.');
    end
    if any(pressure < 0) || any(pressure > 150000)
        error('filterPressure:OutOfRange', 'Pressure must be within [0, 150000] kPa.');
    end

    if nargin < 2, method = "EMA"; end
    if nargin < 3, param = []; end

    [filteredPressure, methodUsed, paramUsed] = applyFilterKernel(pressure, method, param);

    if length(filteredPressure) > 1
        pressureChange = filteredPressure(end) - filteredPressure(1);
    else
        pressureChange = 0.0;
    end

    res = struct( ...
        'rawPressure', pressure, ...
        'filteredPressure', filteredPressure, ...
        'filteringMethod', string(methodUsed), ...
        'filterParameter', paramUsed, ...
        'pressureChange', pressureChange, ...
        'validityStatus', true, ...
        'units', "kPa");
end
