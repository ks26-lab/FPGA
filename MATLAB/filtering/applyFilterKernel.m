function [filtered, methodUsed, paramUsed] = applyFilterKernel(signal, method, param)
% APPLYFILTERKERNEL Core FPGA-friendly filtering kernel.
%
% Supported Methods:
%   - 'EMA'            : Exponential Moving Average: y[k] = alpha*x[k] + (1-alpha)*y[k-1]
%   - 'MOVING_AVERAGE' : Causal Moving Average: y[k] = (1/N) * sum(x[k-i])
%   - 'MEDIAN'         : Sliding window median filter
%   - 'NONE'           : Passthrough (raw data)
%
% Inputs:
%   signal - 1D vector (row or column) or scalar
%   method - char or string: 'EMA', 'MOVING_AVERAGE', 'MEDIAN', 'NONE'
%   param  - Numerical parameter (alpha for EMA; window size N for MA/MEDIAN)
%
% Outputs:
%   filtered   - Processed signal with identical orientation and length
%   methodUsed - Standardized method string
%   paramUsed  - Actual parameter value used

    if isempty(signal)
        filtered = [];
        methodUsed = "NONE";
        paramUsed = 0;
        return;
    end

    if nargin < 2 || isempty(method)
        method = "EMA";
    else
        method = upper(string(method));
    end

    len = length(signal);
    filtered = zeros(size(signal));

    switch method
        case "EMA"
            % Exponential Moving Average: FPGA-friendly fixed-point multiply-accumulate
            if nargin < 3 || isempty(param)
                alpha = 0.25; % Default alpha (power of 2: 2^-2 for hardware bit-shift)
            else
                alpha = double(param);
            end

            if alpha <= 0 || alpha > 1
                error('applyFilterKernel:InvalidAlpha', 'EMA alpha must satisfy 0 < alpha <= 1.');
            end

            paramUsed = alpha;
            methodUsed = "EMA";

            % Initialize filter state with first sample
            filtered(1) = signal(1);
            for k = 2:len
                filtered(k) = alpha * signal(k) + (1.0 - alpha) * filtered(k - 1);
            end

        case "MOVING_AVERAGE"
            % Causal Moving Average: y[k] = 1/N * sum_{i=0}^{N-1} x[k-i]
            if nargin < 3 || isempty(param)
                N = 4; % Default window size (power of 2 for hardware right-shift)
            else
                N = double(param);
            end

            if N < 1 || floor(N) ~= N
                error('applyFilterKernel:InvalidWindowSize', 'Moving Average window size N must be integer >= 1.');
            end

            paramUsed = N;
            methodUsed = "MOVING_AVERAGE";

            % Causal accumulation (FPGA shift-register pipeline)
            for k = 1:len
                startIdx = max(1, k - N + 1);
                window = signal(startIdx:k);
                filtered(k) = sum(window) / length(window);
            end

        case "MEDIAN"
            % Sliding Window Median Filter: Removes isolated salt-and-pepper outliers
            if nargin < 3 || isempty(param)
                N = 3; % Default odd window size
            else
                N = double(param);
            end

            if N < 1 || floor(N) ~= N
                error('applyFilterKernel:InvalidWindowSize', 'Median filter window size N must be integer >= 1.');
            end

            paramUsed = N;
            methodUsed = "MEDIAN";

            halfWin = floor(N / 2);
            for k = 1:len
                wStart = max(1, k - halfWin);
                wEnd = min(len, k + halfWin);
                window = signal(wStart:wEnd);
                filtered(k) = median(window);
            end

        case "NONE"
            filtered = signal;
            methodUsed = "NONE";
            paramUsed = 0;

        otherwise
            error('applyFilterKernel:UnknownMethod', ...
                  'Filter method ''%s'' is not recognized. Use EMA, MOVING_AVERAGE, MEDIAN, or NONE.', method);
    end
end
