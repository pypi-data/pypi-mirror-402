"""DCE API Python SDK - 资讯服务."""

from typing import TYPE_CHECKING, Optional

from ..errors import ValidationError
from ..models import (
    Article,
    GetArticleByPageRequest,
    GetArticleByPageResponse,
)

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_ARTICLE_BY_PAGE = "/dceapi/cms/info/articleByPage"

# 有效的 columnId 值
VALID_COLUMN_IDS = {"244", "245", "246", "248", "1076", "242"}


class NewsService:
    """资讯服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化资讯服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_article_by_page(
        self,
        request: GetArticleByPageRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> GetArticleByPageResponse:
        """分页获取文章列表.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            GetArticleByPageResponse: 文章列表响应

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        # 验证 columnId
        if request.column_id not in VALID_COLUMN_IDS:
            raise ValidationError(
                "column_id",
                f"invalid column_id, must be one of: {', '.join(sorted(VALID_COLUMN_IDS))}",
            )

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_ARTICLE_BY_PAGE,
            body=request,
            result_type=dict,
            trade_type=trade_type,
            lang=lang,
        )
        return self._parse_article_page_response(result)

    def _parse_article_page_response(self, data: dict) -> GetArticleByPageResponse:
        """解析文章列表响应.

        Args:
            data: 原始数据字典

        Returns:
            GetArticleByPageResponse: 文章列表响应对象
        """
        if not isinstance(data, dict):
            return GetArticleByPageResponse(
                column_id="",
                total_count=0,
                result_list=[],
            )

        def parse_articles(items: list) -> list:
            """解析文章列表."""
            articles = []
            for item in items:
                if isinstance(item, dict):
                    article = Article(
                        id=item.get("id", item.get("articleId", "")),
                        title=item.get("title", ""),
                        sub_title=item.get("subTitle", ""),
                        summary=item.get("infoSummary", ""),
                        show_date=item.get("showDate", ""),
                        create_date=item.get("createDate", ""),
                        content=item.get("content", ""),
                        keywords=item.get("keywords", ""),
                        page_name=item.get("pageName", ""),
                        # 新增字段
                        version=item.get("version"),
                        source_id=item.get("sourceId"),
                        release_date=item.get("releaseDate"),
                        entity_type=item.get("entityType"),
                        title_image_url=item.get("titleImageUrl"),
                        article_static_url=item.get("articleStaticUrl"),
                        article_dynamic_url=item.get("articleDynamicUrl"),
                    )
                    articles.append(article)
            return articles

        return GetArticleByPageResponse(
            column_id=data.get("columnId", ""),
            total_count=int(data.get("totalCount", 0)),
            result_list=parse_articles(data.get("resultList", [])),
            # 新增字段
            status=data.get("status"),
            status_info=data.get("statusInfo"),
        )
