nextflow.enable.dsl=2


process PrepareQcTargets {

    // cache false

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    secret 'SYNAPSE_AUTH_TOKEN'

    input:
    path input_csv

    output:
    path "targets/*.json"

    script:
    """
    dcqc.py prepare_targets ${input_csv} targets/
    """
}


process StageQcTargets {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    secret 'SYNAPSE_AUTH_TOKEN'

    input:
    path target_json

    output:
    tuple path(target_json), path("staged/*")

    script:
    """
    dcqc.py stage_target ${target_json} staged/
    """
}


process PrepareQcTests {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    secret 'SYNAPSE_AUTH_TOKEN'

    input:
    tuple path(target_json), path(staged_file)

    output:
    tuple path("tests/*"), path(staged_file)

    script:
    """
    dcqc.py prepare_tests ${target_json} tests/
    """
}


process RunInternalQcTest {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    tuple path(test_json), path(staged_file)

    output:
    path "${test_json.baseName}.result.json"

    script:
    """
    dcqc.py run_test ${test_json} ${test_json.baseName}.result.json
    """
}


process PreExternalQcTest {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    tuple path(test_json), path(staged_file)

    output:
    tuple path(test_json), path(staged_file), path("${test_json.baseName}.cmd.json")

    script:
    """
    dcqc.py prepare_cmd ${test_json} ${test_json.baseName}.cmd.json
    """
}


process RunExternalQcTest {

    container "${container}"

    input:
    tuple path(test_json), path(staged_file), val(container), val(cmd)

    output:
    tuple path(test_json), path(".command.out"), path(".command.err"), path(".exitcode")

    script:
    """
    ${cmd}
    """
}


process PostExternalQcTest {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    tuple path(test_json), path("std_out.txt"), path("std_err.txt"), path("exit_code.txt")

    output:
    path "${test_json.baseName}.result.json"

    script:
    """
    dcqc.py interpret_cmd ${test_json} ${test_json.baseName}.result.json
    """
}


process TargetJsonReport {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    tuple val(name), path(test_results)

    output:
    path "${name}.qc_report.json"

    script:
    """
    dcqc.py target_report ${name}.qc_report.json *.json
    """

}


process DatasetJsonReport {

    container "sagebionetworks/synapsepythonclient:v2.7.0"

    input:
    path report_jsons

    output:
    path "dataset.qc_report.json"

    script:
    """
    dcqc.py compile_reports dataset.qc_report.json *.json
    """

}


workflow {

    Channel.fromPath(params.input)
        | PrepareQcTargets
        | flatten
        | StageQcTargets
        | PrepareQcTests
        | transpose
        | map { test, staged ->
            parsed = parseJson(test)
            is_internal_test = parsed.is_internal_test
            [is_internal_test, [ test, staged ]]
        }
        | branch { is_internal_test, it ->
            internal: is_internal_test
                return it
            external: !is_internal_test
                return it
        }
        | set { tests }

    tests.internal
        | RunInternalQcTest
        | set { internal_test_results }
    
    tests.external
        | PreExternalQcTest
        | map { test, staged, cmd ->
            parsed = parseJson(cmd)
            [ test, staged, parsed.container, parsed.command ]
        }
        | RunExternalQcTest
        | PostExternalQcTest
        | set { external_test_results }

    internal_test_results
        | mix (external_test_results)
        | map { it ->
            parsed = parseJson(it)
            name = parsed.target.uri.replaceFirst(/.*?:\/\//, "")
            [name, it]
        }
        | groupTuple
        | TargetJsonReport
        | collect
        | DatasetJsonReport
        | view

}


// Utility Functions

def parseJson(file) {
    def parser = new groovy.json.JsonSlurper()
    return parser.parseText(file.text)
}
