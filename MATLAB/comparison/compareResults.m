function comparison = compareResults(matlabResult, fpgaResult, customTolerances)
% COMPARERESULTS Compares MATLAB golden reference model against FPGA hardware results.
%
% Architecture Role:
%   Evaluates numerical fidelity between high-precision float64 MATLAB calculations
%   and FPGA hardware calculations (accounting for fixed-point quantization,
%   rounding, and finite precision).
%
% Syntax:
%   comparison = compareResults(matlabResult, fpgaResult, customTolerances)
%
% Inputs:
%   matlabResult     - Struct returned by runReferenceModel
%   fpgaResult       - Struct returned by Zynq FPGA runtime interface
%   customTolerances - (Optional) Struct specifying custom absolute/relative tolerances
%
% Outputs:
%   comparison       - Struct containing:
%                        .scene
%                        .verdict ("PASS" or "FAIL")
%                        .maxErrorPercent
%                        .fieldsChecked (table / struct of per-field errors)
%                        .intermediateChecked (comparison of intermediate pipeline stages)
%                        .summaryText

    if nargin < 2 || isempty(matlabResult) || isempty(fpgaResult)
        error('compareResults:EmptyInput', 'Both matlabResult and fpgaResult are required.');
    end

    sceneName = string(matlabResult.scene);

    % 1. Default Domain-Specific Tolerances
    % Format: .absTol (absolute), .relTol (relative, fraction e.g. 0.01 = 1%)
    defaultTols = struct();
    defaultTols.depth = struct('absTol', 0.05, 'relTol', 0.02);             % 0.05 m or 2%
    defaultTols.controlOutput = struct('absTol', 0.50, 'relTol', 0.01);     % 0.50 % or 1%
    defaultTols.velocity = struct('absTol', 0.10, 'relTol', 0.02);          % 0.10 m/s
    defaultTols.speedKmh = struct('absTol', 0.50, 'relTol', 0.02);          % 0.50 km/h
    defaultTols.greenTimeSec = struct('absTol', 0.50, 'relTol', 0.02);      % 0.50 sec
    defaultTols.filteredPressure = struct('absTol', 0.10, 'relTol', 0.02);  % 0.10 kPa
    defaultTols.pressureValve = struct('absTol', 0.50, 'relTol', 0.01);     % 0.50 %
    defaultTols.thermalControl = struct('absTol', 0.50, 'relTol', 0.01);    % 0.50 %
    defaultTols.default = struct('absTol', 0.05, 'relTol', 0.02);

    if nargin >= 3 && isstruct(customTolerances)
        % Override defaults if provided
        fn = fieldnames(customTolerances);
        for i = 1:length(fn)
            defaultTols.(fn{i}) = customTolerances.(fn{i});
        end
    end

    % 2. Compare Outputs
    allPassed = true;
    maxErrPct = 0.0;
    outFields = fieldnames(matlabResult.outputs);
    checkedFields = struct();

    for i = 1:length(outFields)
        fname = outFields{i};
        mVal = matlabResult.outputs.(fname);

        if isfield(fpgaResult.outputs, fname)
            fVal = fpgaResult.outputs.(fname);

            if ischar(mVal) || isstring(mVal)
                % Categorical / State comparison
                match = (string(mVal) == string(fVal));
                allPassed = allPassed && match;
                checkedFields.(fname) = struct( ...
                    'matlab', string(mVal), ...
                    'fpga', string(fVal), ...
                    'match', match, ...
                    'passed', match);
            elseif isnumeric(mVal)
                fValNum = double(fVal);
                mValNum = double(mVal);

                absErr = abs(mValNum - fValNum);
                if abs(mValNum) > 1e-6
                    relErr = absErr / abs(mValNum);
                else
                    relErr = absErr; % Zero-safe
                end
                pctErr = relErr * 100.0;
                if pctErr > maxErrPct, maxErrPct = pctErr; end

                % Look up tolerance
                if isfield(defaultTols, fname)
                    tol = defaultTols.(fname);
                else
                    tol = defaultTols.default;
                end

                % Pass if within either absolute OR relative tolerance
                passed = (absErr <= tol.absTol) || (relErr <= tol.relTol);
                allPassed = allPassed && passed;

                checkedFields.(fname) = struct( ...
                    'matlab', mValNum, ...
                    'fpga', fValNum, ...
                    'absError', absErr, ...
                    'relError', relErr, ...
                    'percentError', pctErr, ...
                    'absTol', tol.absTol, ...
                    'passed', passed);
            end
        end
    end

    % 3. Compare Intermediate Stages (where present)
    intermediateChecked = struct();
    if isfield(matlabResult, 'intermediate') && isfield(fpgaResult, 'intermediate')
        iFields = fieldnames(matlabResult.intermediate);
        for i = 1:length(iFields)
            iname = iFields{i};
            if isfield(fpgaResult.intermediate, iname)
                mI = double(matlabResult.intermediate.(iname));
                fI = double(fpgaResult.intermediate.(iname));
                iAbs = abs(mI - fI);
                intermediateChecked.(iname) = struct( ...
                    'matlab', mI, ...
                    'fpga', fI, ...
                    'absError', iAbs);
            end
        end
    end

    % 4. Formulate Verdict
    if allPassed
        verdict = "PASS";
    else
        verdict = "FAIL";
    end

    comparison = struct( ...
        'scene', sceneName, ...
        'verdict', verdict, ...
        'allPassed', allPassed, ...
        'maxErrorPercent', maxErrPct, ...
        'outputsChecked', checkedFields, ...
        'intermediateChecked', intermediateChecked, ...
        'timestamp', datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
end
