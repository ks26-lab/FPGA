function res = filterDepth(depth, method, param)
% FILTERDEPTH Filters underwater depth sensor signal.
%
% Inputs:
%   depth  - Raw depth in meters [0, 11500] (scalar or vector)
%   method - (Optional) 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param  - (Optional) Filter parameter (alpha or window size)
%
% Outputs:
%   res    - struct containing:
%              .rawDepth
%              .filteredDepth
%              .filteringMethod
%              .filterParameter
%              .depthChange
%              .validityStatus
%              .units

    if nargin < 1 || isempty(depth)
        error('filterDepth:EmptyInput', 'Depth signal cannot be empty.');
    end
    if ~isnumeric(depth) || any(isnan(depth(:))) || any(isinf(depth(:)))
        error('filterDepth:InvalidSignal', 'Depth contains non-numeric, NaN, or Inf values.');
    end
    if any(depth < 0) || any(depth > 11500)
        error('filterDepth:OutOfRange', 'Depth must be within [0, 11500] meters.');
    end

    if nargin < 2, method = "EMA"; end
    if nargin < 3, param = []; end

    % Apply core FPGA-reproducible filter kernel
    [filteredDepth, methodUsed, paramUsed] = applyFilterKernel(depth, method, param);

    % Calculate total change across the observed window
    if length(filteredDepth) > 1
        depthChange = filteredDepth(end) - filteredDepth(1);
    else
        depthChange = 0.0;
    end

    res = struct( ...
        'rawDepth', depth, ...
        'filteredDepth', filteredDepth, ...
        'filteringMethod', string(methodUsed), ...
        'filterParameter', paramUsed, ...
        'depthChange', depthChange, ...
        'validityStatus', true, ...
        'units', "meters");
end
