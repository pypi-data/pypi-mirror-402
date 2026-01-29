"""DCE API Python SDK - 交割服务."""

from typing import TYPE_CHECKING, List, Optional

from ..errors import ValidationError
from ..models import (
    BondedDelivery,
    BondedDeliveryRequest,
    DeliveryCost,
    DeliveryData,
    DeliveryDataRequest,
    DeliveryMatch,
    DeliveryMatchRequest,
    FactorySpotAgioQuote,
    PlywoodDeliveryCommodity,
    RollDeliverySellerIntention,
    RollDeliverySellerIntentionRequest,
    TcCongregateDelivery,
    TcCongregateDeliveryRequest,
    WarehousePremium,
    WarehousePremiumResponse,
    WarehouseReceipt,
    WarehouseReceiptRequest,
    WarehouseReceiptResponse,
)

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_DELIVERY_DATA = "/dceapi/forward/publicweb/deliverystat/delivery"
PATH_GET_DELIVERY_MATCH = "/dceapi/forward/publicweb/deliverystat/deliveryMatch"
PATH_GET_WAREHOUSE_RECEIPT = "/dceapi/forward/publicweb/dailystat/wbillWeeklyQuotes"
PATH_GET_DELIVERY_COST = "/dceapi/forward/publicweb/deliverypara/deliveryCosts"
PATH_GET_WAREHOUSE_PREMIUM = "/dceapi/forward/publicweb/deliverypara/floatingAgio"
# 新增端点
PATH_GET_TC_CONGREGATE_DELIVERY = "/dceapi/forward/publicweb/DeliveryStatistics/tcCongregateDeliveryQuotes"
PATH_GET_ROLL_DELIVERY_SELLER = "/dceapi/forward/publicweb/DeliveryStatistics/rollDeliverySellerIntention"
PATH_GET_BONDED_DELIVERY = "/dceapi/forward/publicweb/quotesdata/bondedDelivery"
PATH_GET_TD_BONDED_DELIVERY = "/dceapi/forward/publicweb/quotesdata/tdBondedDelivery"
PATH_GET_PLYWOOD_DELIVERY_COMMODITY = "/dceapi/forward/publicweb/deliverystat/queryPlywoodDeliveryCommodity"
PATH_GET_FACTORY_SPOT_AGIO = "/dceapi/forward/publicweb/quotesdata/queryFactorySpotAgioQuotes"


class DeliveryService:
    """交割服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化交割服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_delivery_data(
        self,
        request: DeliveryDataRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[DeliveryData]:
        """获取交割数据.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[DeliveryData]: 交割数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DELIVERY_DATA,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_delivery_data(result)

    def _parse_delivery_data(self, data: list) -> List[DeliveryData]:
        """解析交割数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    DeliveryData(
                        variety=item.get("variety", ""),
                        contract_id=item.get("contractId", ""),
                        delivery_date=item.get("deliveryDate", ""),
                        delivery_qty=int(item.get("deliveryQty", 0)),
                        delivery_amt=item.get("deliveryAmt", ""),
                        variety_en=item.get("varietyEn"),
                    )
                )
        return result

    def get_delivery_match(
        self,
        request: DeliveryMatchRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[DeliveryMatch]:
        """获取交割配对数据.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[DeliveryMatch]: 交割配对列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DELIVERY_MATCH,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_delivery_match(result)

    def _parse_delivery_match(self, data: list) -> List[DeliveryMatch]:
        """解析交割配对数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    DeliveryMatch(
                        contract_id=item.get("contractId", ""),
                        match_date=item.get("matchDate", ""),
                        buy_member_id=item.get("buyMemberId", ""),
                        sell_member_id=item.get("sellMemberId", ""),
                        delivery_qty=int(item.get("deliveryQty", 0)),
                        delivery_price=item.get("deliveryPrice", ""),
                    )
                )
        return result

    def get_warehouse_receipt(
        self,
        request: WarehouseReceiptRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> WarehouseReceiptResponse:
        """获取仓单日报数据.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            WarehouseReceiptResponse: 仓单日报响应

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_WAREHOUSE_RECEIPT,
            body=request,
            result_type=dict,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_warehouse_receipt(result)

    def _parse_warehouse_receipt(self, data: dict) -> WarehouseReceiptResponse:
        """解析仓单日报数据."""
        if not isinstance(data, dict):
            return WarehouseReceiptResponse(entity_list=[])

        entity_list = []
        for item in data.get("entityList", []):
            if isinstance(item, dict):
                entity_list.append(
                    WarehouseReceipt(
                        variety=item.get("variety", ""),
                        wh_abbr=item.get("whAbbr", ""),
                        last_wbill_qty=int(item.get("lastWbillQty", 0)),
                        wbill_qty=int(item.get("wbillQty", 0)),
                        diff=int(item.get("diff", 0)),
                        variety_order=item.get("varietyOrder"),
                        group_code_order=item.get("groupCodeOrder"),
                        wh_code_order=item.get("whCodeOrder"),
                        wh_type=item.get("whType"),
                        gen_date=item.get("genDate"),
                        delivery_abbr=item.get("deliveryAbbr"),
                        reg_wbill_qty=item.get("regWbillQty"),
                        logout_wbill_qty=item.get("logoutWbillQty"),
                    )
                )

        return WarehouseReceiptResponse(
            entity_list=entity_list,
            if_agio_flag=data.get("ifAgioFlag"),
            agio_deli_type=data.get("agioDeliType"),
            if_agio_brand_flag=data.get("ifAgioBrandFlag"),
        )

    def get_delivery_cost(
        self,
        variety_id: str,
        variety_type: str = "0",
        lang: Optional[str] = None,
    ) -> List[DeliveryCost]:
        """获取交割费用标准.

        Args:
            variety_id: 品种id，全部为all
            variety_type: 0=实物交割费用标准, 1=月均价交割费用标准
            lang: 语言（覆盖配置）

        Returns:
            List[DeliveryCost]: 交割费用列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if not variety_id:
            raise ValidationError("variety_id", "variety_id is required")

        req_body = {
            "varietyId": variety_id,
            "varietyType": variety_type,
            "lang": lang or "zh",
        }

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DELIVERY_COST,
            body=req_body,
            result_type=list,
            lang=lang,
        )

        return self._parse_delivery_cost(result)

    def _parse_delivery_cost(self, data: list) -> List[DeliveryCost]:
        """解析交割费用数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    DeliveryCost(
                        variety=item.get("variety", ""),
                        earnest_rate=item.get("earnestRate", ""),
                        unit=item.get("unit", ""),
                        delivery_fee=item.get("deliveryFee", ""),
                        fee_rate=item.get("feeRate", ""),
                        start_date=item.get("startDate", ""),
                        end_date=item.get("endDate", ""),
                    )
                )
        return result

    def get_warehouse_premium(
        self,
        variety_id: str,
        trade_date: str,
    ) -> WarehousePremiumResponse:
        """获取仓库升贴水.

        Args:
            variety_id: 品种id，全部为all
            trade_date: 交易日

        Returns:
            WarehousePremiumResponse: 仓库升贴水响应

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if not variety_id:
            raise ValidationError("variety_id", "variety_id is required")
        if not trade_date:
            raise ValidationError("trade_date", "trade_date is required")

        req_body = {
            "varietyId": variety_id,
            "tradeDate": trade_date,
        }

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_WAREHOUSE_PREMIUM,
            body=req_body,
            result_type=dict,
        )

        return self._parse_warehouse_premium(result)

    def _parse_warehouse_premium(self, data: dict) -> WarehousePremiumResponse:
        """解析仓库升贴水数据."""
        if not isinstance(data, dict):
            return WarehousePremiumResponse(entity_list=[])

        entity_list = []
        for item in data.get("entityList", []):
            if isinstance(item, dict):
                entity_list.append(
                    WarehousePremium(
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        wh_name=item.get("whName", ""),
                        avg_agio=item.get("avgAgio", ""),
                        valid_date=item.get("validDate"),
                        wh_code=item.get("whCode"),
                        wh_group_abbr=item.get("whGroupAbbr"),
                        brand_abbr=item.get("brandAbbr"),
                    )
                )

        return WarehousePremiumResponse(
            entity_list=entity_list,
            if_agio_flag=data.get("ifAgioFlag"),
            agio_deli_type=data.get("agioDeliType"),
            if_agio_brand_flag=data.get("ifAgioBrandFlag"),
        )

    def get_tc_congregate_delivery(
        self,
        request: TcCongregateDeliveryRequest,
    ) -> List[TcCongregateDelivery]:
        """获取一次性交割卖方仓单查询.

        Args:
            request: 请求参数

        Returns:
            List[TcCongregateDelivery]: 一次性交割卖方仓单列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_TC_CONGREGATE_DELIVERY,
            body=request,
            result_type=list,
        )

        return self._parse_tc_congregate_delivery(result)

    def _parse_tc_congregate_delivery(
        self, data: list
    ) -> List[TcCongregateDelivery]:
        """解析一次性交割卖方仓单数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    TcCongregateDelivery(
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        contract=item.get("contract", ""),
                        warehouse_name=item.get("warehouseName", ""),
                        wbill_quantity=item.get("wbillQuantity", ""),
                        agreeable_place=item.get("agreeablePlace"),
                        agreeable_brand=item.get("agreeableBrand"),
                        agreeable_quality=item.get("agreeableQuality"),
                        agreeable_quantity=item.get("agreeableQuantity"),
                        agreeable_spread=item.get("agreeableSpread"),
                        contracts=item.get("contracts"),
                        contract_way=item.get("contractWay"),
                        wh_group_name=item.get("whGroupName"),
                    )
                )
        return result

    def get_roll_delivery_seller_intention(
        self,
        request: RollDeliverySellerIntentionRequest,
    ) -> List[RollDeliverySellerIntention]:
        """获取滚动交割卖方交割意向表.

        Args:
            request: 请求参数

        Returns:
            List[RollDeliverySellerIntention]: 滚动交割卖方意向列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_ROLL_DELIVERY_SELLER,
            body=request,
            result_type=list,
        )

        return self._parse_roll_delivery_seller(result)

    def _parse_roll_delivery_seller(
        self, data: list
    ) -> List[RollDeliverySellerIntention]:
        """解析滚动交割卖方意向数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    RollDeliverySellerIntention(
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        contract=item.get("contract", ""),
                        type=item.get("type", ""),
                        warehouse_code=item.get("warehouseCode", ""),
                        warehouse_name=item.get("warehouseName", ""),
                        quantity=item.get("quantity", ""),
                        trade_date=item.get("tradeDate", ""),
                        delivery_way=item.get("deliveryWay", ""),
                        agreeable_place=item.get("agreeablePlace"),
                        agreeable_brand=item.get("agreeableBrand"),
                        agreeable_quality=item.get("agreeableQuality"),
                        agreeable_quantity=item.get("agreeableQuantity"),
                        agreeable_spread=item.get("agreeableSpread"),
                        contracts=item.get("contracts"),
                        contract_way=item.get("contractWay"),
                        wh_group_name=item.get("whGroupName"),
                    )
                )
        return result

    def get_bonded_delivery(
        self,
        request: BondedDeliveryRequest,
    ) -> List[BondedDelivery]:
        """获取交割结算价.

        Args:
            request: 请求参数

        Returns:
            List[BondedDelivery]: 交割结算价列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_BONDED_DELIVERY,
            body=request,
            result_type=list,
        )

        return self._parse_bonded_delivery(result)

    def get_td_bonded_delivery(
        self,
        request: BondedDeliveryRequest,
    ) -> List[BondedDelivery]:
        """获取保税交割结算价.

        Args:
            request: 请求参数

        Returns:
            List[BondedDelivery]: 保税交割结算价列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_TD_BONDED_DELIVERY,
            body=request,
            result_type=list,
        )

        return self._parse_bonded_delivery(result)

    def _parse_bonded_delivery(self, data: list) -> List[BondedDelivery]:
        """解析交割结算价数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    BondedDelivery(
                        delivery_date=item.get("deliveryDate", ""),
                        delivery_way=item.get("deliveryWay", ""),
                        variety_id=item.get("varietyId", ""),
                        contract_id=item.get("contractId", ""),
                        delivery_price=item.get("deliveryPrice", ""),
                        wh_abbr=item.get("whAbbr"),
                        bonded_delivery_price=item.get("bondedDeliveryPrice"),
                    )
                )
        return result

    def get_plywood_delivery_commodity(self) -> List[PlywoodDeliveryCommodity]:
        """获取胶合板交割商品查询.

        Returns:
            List[PlywoodDeliveryCommodity]: 胶合板交割商品列表

        Raises:
            APIError: API 错误
        """
        result = self.client.do_request(
            method="POST",
            path=PATH_GET_PLYWOOD_DELIVERY_COMMODITY,
            body={},
            result_type=list,
        )

        return self._parse_plywood_delivery_commodity(result)

    def _parse_plywood_delivery_commodity(
        self, data: list
    ) -> List[PlywoodDeliveryCommodity]:
        """解析胶合板交割商品数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    PlywoodDeliveryCommodity(
                        apply_id=item.get("applyId", ""),
                        wh_name=item.get("whName", ""),
                        wh_abbr=item.get("whAbbr", ""),
                        upload_file_id=item.get("uploadFileId", ""),
                        file_size=int(item.get("fileSize", 0)),
                        upload_file_name=item.get("uploadFileName", ""),
                    )
                )
        return result

    def get_factory_spot_agio_quotes(self) -> List[FactorySpotAgioQuote]:
        """获取纤维板厂库自报换货差价.

        Returns:
            List[FactorySpotAgioQuote]: 换货差价列表

        Raises:
            APIError: API 错误
        """
        result = self.client.do_request(
            method="POST",
            path=PATH_GET_FACTORY_SPOT_AGIO,
            body={},
            result_type=list,
        )

        return self._parse_factory_spot_agio(result)

    def _parse_factory_spot_agio(self, data: list) -> List[FactorySpotAgioQuote]:
        """解析纤维板厂库自报换货差价数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(
                    FactorySpotAgioQuote(
                        seq_no=item.get("seqNo", ""),
                        wh_abbr=item.get("whAbbr", ""),
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        wh_code=item.get("whCode"),
                        bh=item.get("bh"),
                        mdmin=item.get("mdmin"),
                        mdmax=item.get("mdmax"),
                        jq=item.get("jq"),
                        agio=item.get("agio"),
                        min_exchange_amount=item.get("minExchangeAmount"),
                        wh_addr=item.get("whAddr"),
                        connect_person=item.get("connectPerson"),
                        tel=item.get("tel"),
                    )
                )
        return result
