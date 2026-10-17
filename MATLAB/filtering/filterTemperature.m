function res = filterTemperature(temperature, method, param)
% FILTERTEMPERATURE Filters environment temperature sensor signal.
%
% Inputs:
%   temperature - Raw temperature in degrees Celsius [-273.15, 300] (scalar or vector)
%   method      - (Optional) 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param       - (Optional) Filter parameter (alpha or window size)
%
% Outputs:
%   res         - struct containing:
%                   .rawTemperature
%                   .filteredTemperature
%                   .filteringMethod
%                   .filterParameter
%                   .temperatureChange
%                   .validityStatus
%                   .units

    if nargin < 1 || isempty(temperature)
        error('filterTemperature:EmptyInput', 'Temperature signal cannot be empty.');
    end
    if ~isnumeric(temperature) || any(isnan(temperature(:))) || any(isinf(temperature(:)))
        error('filterTemperature:InvalidSignal', 'Temperature contains non-numeric, NaN, or Inf values.');
    end
    if any(temperature < -273.15) || any(temperature > 300)
        error('filterTemperature:OutOfRange', 'Temperature must be within [-273.15, 300] °C.');
    end

    if nargin < 2, method = "EMA"; end
    if nargin < 3, param = []; end

    [filteredTemp, methodUsed, paramUsed] = applyFilterKernel(temperature, method, param);

    if length(filteredTemp) > 1
        temperatureChange = filteredTemp(end) - filteredTemp(1);
    else
        temperatureChange = 0.0;
    end

    res = struct( ...
        'rawTemperature', temperature, ...
        'filteredTemperature', filteredTemp, ...
        'filteringMethod', string(methodUsed), ...
        'filterParameter', paramUsed, ...
        'temperatureChange', temperatureChange, ...
        'validityStatus', true, ...
        'units', "degC");
end
