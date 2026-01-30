#ifndef OP_PROTO_H_
#define OP_PROTO_H_

#include "graph/operator_reg.h"
#include "register/op_impl_registry.h"

namespace ge {

REG_OP(AllFinite)
    .INPUT(gradient, ge::TensorType::ALL())
    .OUTPUT(is_finite, ge::TensorType::ALL())
    .OP_END_FACTORY_REG(AllFinite);

}

#endif
