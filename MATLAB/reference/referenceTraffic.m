function result = referenceTraffic(inputData)
% REFERENCETRAFFIC Golden reference mathematical model for intelligent traffic control.
%
% Mathematical Model:
%   1. Filter Velocity:
%      v_filt = exponentialFilter(v_raw, alpha)
%   2. Speed Conversion:
%      speedKmh = v_filt * 3.6
%   3. Green Time Allocation (Traffic signal dynamic optimization):
%      queueTerm = Kq * queueLength
%      speedTerm = Kv * (speedKmh - 30.0)
%      rawGreen = T0 + queueTerm - speedTerm
%      greenTime = clamp(rawGreen, Tmin, Tmax)
%   4. Congestion State:
%      speedKmh < 25.0 => "CONGESTED"
%      speedKmh > 60.0 => "FREE_FLOW"
%      otherwise       => "OPTIMAL"

    % Explicit control coefficients
    T0   = 30.0;  % Base green time (seconds)
    Tmin = 10.0;  % Minimum green time (seconds)
    Tmax = 90.0;  % Maximum green time (seconds)
    Kq   = 1.50;  % Queue weight (sec / vehicle)
    Kv   = 0.50;  % Speed sensitivity (sec / km/h)
    alpha = 0.25; % Filter alpha

    rawVel = double(inputData.velocity);
    if length(rawVel) > 1, v_in = rawVel(end); else, v_in = rawVel; end

    if isfield(inputData, 'queueLength') && ~isempty(inputData.queueLength)
        queue = double(inputData.queueLength);
    else
        queue = 8.0; % Nominal queue
    end

    % 1. Filter
    if length(rawVel) > 1
        filteredArr = exponentialFilter(rawVel, alpha);
        v_filt = filteredArr(end);
    else
        v_filt = v_in;
    end

    % 2. Conversion
    speedKmh = v_filt * 3.6;

    % 3. Green Time Allocation
    queueTerm = Kq * queue;
    speedTerm = Kv * (speedKmh - 30.0);
    rawGreen = T0 + queueTerm - speedTerm;
    greenTime = max(Tmin, min(Tmax, rawGreen));

    % 4. State
    if speedKmh < 25.0
        stateStr = "CONGESTED";
    elseif speedKmh > 60.0
        stateStr = "FREE_FLOW";
    else
        stateStr = "OPTIMAL";
    end

    outputs = struct();
    outputs.speedKmh = speedKmh;
    outputs.greenTimeSec = greenTime;
    outputs.state = stateStr;

    intermediate = struct();
    intermediate.rawVelocity = v_in;
    intermediate.filteredVelocity = v_filt;
    intermediate.speedKmh = speedKmh;
    intermediate.queueTerm = queueTerm;
    intermediate.speedTerm = speedTerm;
    intermediate.rawGreenTime = rawGreen;

    parameters = struct( ...
        'T0', T0, ...
        'Tmin', Tmin, ...
        'Tmax', Tmax, ...
        'Kq', Kq, ...
        'Kv', Kv, ...
        'filterAlpha', alpha);

    result = struct( ...
        'scene', "traffic", ...
        'status', "OK", ...
        'outputs', outputs, ...
        'intermediate', intermediate, ...
        'parameters', parameters, ...
        'precision', "float64");
end
