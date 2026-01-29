// Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.

// libmathdx's API is subject to change.
// Please contact Math-Libs-Feedback@nvidia.com for usage feedback.

#ifndef MATHDX_CURANDDX_H
#define MATHDX_CURANDDX_H

#include <stddef.h>

#include "libcommondx.h"

#if defined(__cplusplus)
extern "C" {
#endif /* __cplusplus */

/**
 * @brief A cuRANDDx descriptor
 *
 * Represents a configured cuRANDDx device function description.
 */
typedef long long int curanddxDescriptor;

/**
 * @brief Returns the major.minor.patch version of cuRANDDx
 *
 * @param[out] major The major version
 * @param[out] minor The minor version
 * @param[out] patch The patch version
 * @return `COMMONDX_SUCCESS`
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxGetVersion(int* major, int* minor, int* patch) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Distribution type
 *
 * Indicate the random number generation to use. Can be set using \ref CURANDDX_OPERATOR_DISTRIBUTION and further customize using \ref CURANDDX_OPERATOR_NORMAL_METHOD and \ref CURANDDX_OPERATOR_DISTRIBUTION_PARAMETERS .
 * See cuRANDDx distributions in the documentation: https://docs.nvidia.com/cuda/curanddx/api/methods.html#random-number-generation-with-distributions.
 */
typedef enum curanddxDistribution_t {
    /** Uniform bits distribution (raw random bits without transformation) */
    CURANDDX_DISTRIBUTION_UNIFORM_BITS = 0,
    /** Uniform distribution in [0,1) */
    CURANDDX_DISTRIBUTION_UNIFORM = 1,
    /** Normal distribution */
    CURANDDX_DISTRIBUTION_NORMAL = 2,
    /** Log-normal distribution */
    CURANDDX_DISTRIBUTION_LOG_NORMAL = 3,
    /** Poisson distribution */
    CURANDDX_DISTRIBUTION_POISSON = 4,
} curanddxDistribution;

/**
 * @brief Normal distribution method type
 *
 * Specifies the method to use for normal and log-normal distributions. 
 * Set using \ref CURANDDX_OPERATOR_NORMAL_METHOD .
 * See cuRANDDx normal distribution documentation: https://docs.nvidia.com/cuda/curanddx/api/methods.html#normal-distribution
 */
typedef enum curanddxNormalMethod_t {
    /** Inverse cumulative distribution function (ICDF), generating one value at a time */
    CURANDDX_NORMAL_METHOD_ICDF = 0,
    /** Box-Muller method, requiring two input values and generating two output values */
    CURANDDX_NORMAL_METHOD_BOX_MULLER = 1,
} curanddxNormalMethod;

/**
 * @brief Generation method type
 *
 * Specifies which generation method to use for cuRANDDx distributions. 
 * Set using \ref CURANDDX_OPERATOR_GENERATE_METHOD .
 * See cuRANDDx execution methods in the documentation: https://docs.nvidia.com/cuda/curanddx/api/methods.html
 */
typedef enum curanddxGenerateMethod_t {
    /** Generate single value (invalid for Philox with some distributions) */
    CURANDDX_GENERATE_METHOD_SINGLE = 0,
    /** Generate two values (for Box-Muller or Philox double precision) */
    CURANDDX_GENERATE_METHOD_PAIR = 1,
    /** Generate four values (for Philox generator) */
    CURANDDX_GENERATE_METHOD_QUAD = 2,
} curanddxGenerateMethod;

/**
 * @brief Generator type
 *
 * Matches cuRANDDx generator kinds. Set using \ref CURANDDX_OPERATOR_GENERATOR .
 * See cuRANDDx generators in the documentation: https://docs.nvidia.com/cuda/curanddx/api/description_ops.html#generator-operator-label
 */
typedef enum curanddxGenerator_t {
    CURANDDX_GENERATOR_XORWOW = 0,
    CURANDDX_GENERATOR_MRG32K3A = 1,
    CURANDDX_GENERATOR_PHILOX4_32 = 2,
    CURANDDX_GENERATOR_PCG = 3,
    CURANDDX_GENERATOR_SOBOL32 = 4,
    CURANDDX_GENERATOR_SCRAMBLED_SOBOL32 = 5,
    CURANDDX_GENERATOR_SOBOL64 = 6,
    CURANDDX_GENERATOR_SCRAMBLED_SOBOL64 = 7,
} curanddxGenerator;

/**
 * @brief Operators
 *
 * The set of supported curandDx operators.
 */
typedef enum curanddxOperatorType_t {
    /** Operator data type: \ref curanddxGenerator_t.
     * Operator definition: required */
    CURANDDX_OPERATOR_GENERATOR = 0,
    /** Operator data type: `long long int`.
     * Expected content: number of philox rounds when generator is PHILOX.
     * See https://docs.nvidia.com/cuda/curanddx/api/description_ops.html#philoxrounds-operator.
     * Operator definition: optional (default is 10) */
    CURANDDX_OPERATOR_PHILOX_ROUNDS = 1,
    /** Operator data type: `long long int`.
     * Expected content: 700 (Volta), 800 (Ampere), 890, 900, 1000, 1200, ...
     * Operator definition: required */
    CURANDDX_OPERATOR_SM = 2,
    /** Operator data type: \ref commondxExecution_t.
     * Only support \ref COMMONDX_EXECUTION_THREAD.
     * Operator definition: required */
    CURANDDX_OPERATOR_EXECUTION = 3,
    /** Operator data type: \ref curanddxDistribution_t.
     * Indicate which distribution to use.
     * Operator definition: required */
    CURANDDX_OPERATOR_DISTRIBUTION = 4,
    /** Operator data type: \ref commondxValueType_t.
     * Expected content: scale output element value type (e.g., COMMONDX_R_32F for float).
     * The actual output type is determined by this operator and by \ref CURANDDX_OPERATOR_GENERATE_METHOD.
     * Operator definition: optional */
    CURANDDX_OPERATOR_OUTPUT_TYPE = 5,
    /** Operator data type: \ref curanddxGenerateMethod_t.
     * Expected content: generation method (generate, generate2, generate4).
     * Combined with \ref CURANDDX_OPERATOR_OUTPUT_TYPE this determines the output element types.
     * Operator definition: required */
    CURANDDX_OPERATOR_GENERATE_METHOD = 6,
    /** Operator data type: \ref curanddxNormalMethod_t.
     * Expected content: normal distribution method (ICDF or Box-Muller).
     * Operator definition: optional */
    CURANDDX_OPERATOR_NORMAL_METHOD = 7,
    /** Operator data type: bit fields of xor'ed \ref curanddxDeviceFunctionType_t.
     * Expected content: what device functions to generate.
     * Operator definition: required. */
    CURANDDX_OPERATOR_DEVICE_FUNCTIONS = 8,
    /** Operator data type: double (one or two).
     * Expected content: the parameters of the distribution:
     * - For \ref CURANDDX_DISTRIBUTION_UNIFORM : the minimum and maximum (default: 0 and 1).
     * - For \ref CURANDDX_DISTRIBUTION_NORMAL : the mean and standard deviation (default: 0 and 1).
     * - For \ref CURANDDX_DISTRIBUTION_LOG_NORMAL : the mean and standard deviation (default: 0 and 1).
     * - For \ref CURANDDX_DISTRIBUTION_POISSON : lambda (default: 1).
     * Operator definition: optional. */
    CURANDDX_OPERATOR_DISTRIBUTION_PARAMETERS = 9,
} curanddxOperatorType;

/**
 * @brief Device functions.
 *
 * The set of supported device functions. Must be passed using \ref CURANDDX_OPERATOR_DEVICE_FUNCTIONS and can be 
 * xor'ed to indicate that libmathdx should generate multiple device functions.
 */
typedef enum curanddxDeviceFunctionType_t {
    /** Generate random numbers using pre-initialized state.
     * The device function has signatue `void(void* state, vector_output_type* out)`.
     * `vector_output_type` is specified by \ref CURANDDX_OPERATOR_OUTPUT_TYPE and \ref CURANDDX_OPERATOR_GENERATE_METHOD.
     * See also https://docs.nvidia.com/cuda/curanddx/api/methods.html#random-number-generation-with-distributions 
     * and \ref CURANDDX_TRAIT_SYMBOL_GENERATE_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_GENERATE = 1 << 1,
    /** State initialization function for pseudorandom generators.
     * The device function has signature `void(unsigned long long* seed, unsigned long long* subsequence, offset_type* offset, void* state)`
     * for pseudo-random number generators, and 
     * `void(unsigned int* dim, direction_vector_type* direction_vector, offset_type* offset, scrambled_const_type* scrambled_consts, void* state)`
     * for quasi-random number generators. `offset_type`, `direction_vector_type` and `scrambled_const_type` are all defined like in cuRANDDx.
     * See \ref CURANDDX_TRAIT_SYMBOL_INIT_STATE_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_INIT_STATE = 1 << 2,
    /** State destruction function for pseudorandom generators.
     * The device function has signature `void(void* state)`.
     * See \ref CURANDDX_TRAIT_SYMBOL_DESTROY_STATE_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_DESTROY_STATE = 1 << 3,
    /** Skip offset function (valid for all generators except scrambled SOBOL).
     * The device function has signature `void(void* state, offset_type* n)`.
     * See \ref CURANDDX_TRAIT_SYMBOL_SKIP_OFFSET_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_SKIP_OFFSET = 1 << 4,
    /** Skip subsequence function (valid for pseudorandom generators).
     * The device function has signature `void(void* state, unsigned long long* n)`.
     * See \ref CURANDDX_TRAIT_SYMBOL_SKIP_SUBSEQUENCE_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_SKIP_SUBSEQUENCE = 1 << 5,
    /** Skip sequence function (valid for MRG32K3A generator only).
     * The device function has signature `void(void* state, unsigned long long* n)`.
     * See \ref CURANDDX_TRAIT_SYMBOL_SKIP_SEQUENCE_NAME.
     */
    CURANDDX_DEVICE_FUNCTION_SKIP_SEQUENCE = 1 << 6,
} curanddxDeviceFunctionType;

/**
 * @brief Traits
 *
 * The set of supported types of traits that can be accessed from finalized sources
 * that use curanddx.
 */
typedef enum curanddxTraitType_t {
    /** Trait data type: C-string.
     * Value: \ref CURANDDX_DEVICE_FUNCTION_GENERATE symbol name. */
    CURANDDX_TRAIT_SYMBOL_GENERATE_NAME = 0,
    /** Trait data type: C-string.
    * Value: \ref CURANDDX_DEVICE_FUNCTION_INIT_STATE symbol name. */
    CURANDDX_TRAIT_SYMBOL_INIT_STATE_NAME = 1,
    /** Trait data type: C-string.
     * Value: \ref CURANDDX_DEVICE_FUNCTION_DESTROY_STATE symbol name. */
    CURANDDX_TRAIT_SYMBOL_DESTROY_STATE_NAME = 2,
    /** Trait data type: C-string.
     * Value: \ref CURANDDX_DEVICE_FUNCTION_SKIP_OFFSET symbol name. */
    CURANDDX_TRAIT_SYMBOL_SKIP_OFFSET_NAME = 3,
    /** Trait data type: C-string.
     * Value: \ref CURANDDX_DEVICE_FUNCTION_SKIP_SUBSEQUENCE symbol name. */
    CURANDDX_TRAIT_SYMBOL_SKIP_SUBSEQUENCE_NAME = 4,
    /** Trait data type: C-string.
     * Value: \ref CURANDDX_DEVICE_FUNCTION_SKIP_SEQUENCE symbol name. */
    CURANDDX_TRAIT_SYMBOL_SKIP_SEQUENCE_NAME = 5,
    /** Trait data type: `long long int`.
     * Value: RNG state size in bytes. */
    CURANDDX_TRAIT_STATE_SIZE = 6,
    /** Trait data type: `long long int`.
     * Value: RNG state alignment in bytes. */
    CURANDDX_TRAIT_STATE_ALIGNMENT = 7,
} curanddxTraitType;


/**
 * @brief Creates a cuRANDDx descriptor.
 * @param[in,out] handle A pointer to a descriptor handle. As output, an initialized cuRANDDx descriptor.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxCreateDescriptor(curanddxDescriptor* handle)
    LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Sets a C-string option on a cuRANDDx descriptor.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] opt The option to set.
 * @param[in] value The value for the option.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxSetOptionStr(curanddxDescriptor handle,
                                                                    commondxOption opt,
                                                                    const char* value) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Sets one or more C-string option on a cuRANDDX descriptor
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] opt The option to set.
 * @param[in] count The number of options.
 * @param[in] values An array of `count` C-strings.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxSetOptionStrs(curanddxDescriptor handle,
                                                                      commondxOption opt,
                                                                      size_t count,
                                                                      const char** values) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Sets an integer operator on a cuRANDDx descriptor.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] op The operator to set.
 * @param[in] value A value for the operator.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxSetOperatorInt64(curanddxDescriptor handle,
                                                                         curanddxOperatorType op,
                                                                         long long int value) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Sets the parameters for the distribution.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] op The operator to set. Only supports \ref CURANDDX_OPERATOR_DISTRIBUTION_PARAMETERS .
 * @param[in] count The number of parameters. Must be 1 or 2.
 * @param[in] values The parameters.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxSetOperatorDoubles(curanddxDescriptor handle,
                                                                           curanddxOperatorType op,
                                                                           size_t count,
                                                                           double* values) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns the size of a C-string trait value.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] trait A trait to query the descriptor for.
 * @param[out] size The size of the C-string value for the trait (including the `\0`).
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxGetTraitStrSize(curanddxDescriptor handle,
                                                                          curanddxTraitType trait,
                                                                          size_t* size) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns a C-string trait value.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] trait A trait to query the descriptor for.
 * @param[in] size The size of the C-string, output from \ref curanddxGetTraitStrSize .
 * @param[out] value The C-string trait value.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxGetTraitStr(curanddxDescriptor handle,
                                                                      curanddxTraitType trait,
                                                                      size_t size,
                                                                      char* value) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns an integer trait value.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @param[in] trait A trait to query the descriptor for.
 * @param[out] value The trait value.
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxGetTraitInt64(curanddxDescriptor handle,
                                                                      curanddxTraitType trait,
                                                                      long long int* value) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Fills a code handle with the descriptor's device function code.
 * @param[out] code A code handle output from \ref commondxCreateCode .
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxFinalizeCode(commondxCode code, curanddxDescriptor handle)
    LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Destroys a cuRANDDx descriptor.
 * @param[in] handle A cuRANDDx descriptor, output of \ref curanddxCreateDescriptor .
 * @return `COMMONDX_SUCCESS` on success, or an error code.
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL curanddxDestroyDescriptor(curanddxDescriptor handle)
    LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts an operator enum to a human readable C-string.
 * @param[in] op An operator enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxOperatorTypeToStr(curanddxOperatorType op) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts a distribution enum to a human readable C-string.
 * @param[in] dist A distribution enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxDistributionToStr(curanddxDistribution dist) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts a generator enum to a human readable C-string.
 * @param[in] generator A generator enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxGeneratorToStr(curanddxGenerator generator) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts a generate method enum to a human readable C-string.
 * @param[in] generate_method A generate method enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxGenerateMethodToStr(curanddxGenerateMethod generate_method) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts a normal method enum to a human readable C-string.
 * @param[in] normal_method A normal method enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxNormalMethodToStr(curanddxNormalMethod normal_method) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Converts a trait enum to a human readable C-string.
 * @param[in] trait A trait enum.
 * @return A human readable C-string.
 */
LIBMATHDX_API const char* LIBMATHDX_CALL curanddxTraitTypeToStr(curanddxTraitType trait) LIBMATHDX_API_NOEXCEPT;

#if defined(__cplusplus)
} // extern "C"
#endif /* __cplusplus */

#endif // MATHDX_CURANDDX_H
