# data-sheet-summary

### Description

此为python编写的一个小脚本，其功能：

* 统计销售数据表
* 核对花名册补充/删除信息

### Software Architecture

这是一个 python script.

其工作原理为：

1. 在数据表按照config中的filter_cols做筛选
2. 分别根据role_groups，和group_columns分组，同时根据agg_columns做合并
3. 按照role_groups先后确定优先级关系，高优先级职位不出现在低优先级统计中
4. 与花名册合并，花名册中没有信息的数据删除。
5. 按照output_cols_map的对应关系重新定义列名。

### Installation

1. xxxx
2. xxxx
3. xxxx

### Instructions

json文件中为设置项，默认配置如下

```json
{
            "input_file": "input.xlsx",
            "index_file": "index.xlsx",
            "output_file_name": "summary_output.xlsx",
            "sheet_name": "Sheet1",
            "filter_cols": {"月份": ["1月", "2月"]},
            "role_groups": ["销售主管", "销售代表"],
            "group_columns": ["大类"],
            "agg_columns": {
                "2023金额": "sum",
                "2024金额": "sum"},
            "output_cols_map": {
                "部门": "部门",
                "区域": "区域",
                "姓名": "姓名",
                "职务/岗位": "职务/岗位",
                "大类": "大类",
                "2023金额": "2023年1-2月累计金额",
                "2024金额": "2024年1-2月累计金额"}
        }
```

其中：

1. input_file是数据表, sheet_name是数据表中需要的子表名, index_file是花名册
2. sep_groups_col/group_columns/agg_columns是数据表合并后的保留的列
3. sep_groups_col的第一个必须对应销售主管
4. agg_columns就是数据表中的合并项, 其必须存在于output_columns_map和数据表的列名中
5. output_columns_map后者是输出表中需要填写的列名,前者是input_file和index_file对应的列名
6. output_cols_map中的前几个列名最好不要改
