# LinkedModel

我个人不太喜欢ORM，
而且Python有很多已有的ORM框架，
所以drape框架没有提供ORM模块。

但是drape提供了一个LinkedModel，
对SQL语句做了封装，
以简化SQL操作，
完成增删改查。

函数名基本上与SQL语句中的关键字保持一致

## import与构造函数

给构造函数传递表名就可以得到一个LinkedModel对象

    from drape.model import LinkedModel
    user_model = LinkedModel('user')

## 增

使用insert方法来插入一条数据

    user_model.insert(
        username='John',
        age=26,
        company='JDMD'
    )

同时插入多条数据

    user_model.insert(
        username=['Jack', 'Peter'],
        age=[29,31],
        company=['CPF', 'JRD']
    )

这种语法比较不易读，不好维护，不建议使用。

## 删

    user_model.where(
        username='Peter'
    ).delete()

## 改

    user_model.where(
        username='Jack'
    ).update(
        age=23,
        company='JDMD'
    )

## 查

### 查多条

    user_list = user_model.where(
        company='JDMD'
    ).select()

### 查单条

    user_info = user_model.where(
        username='John'
    ).find()

### 查数量

    user_count = user_model.where(
        company='JDMD'
    ).count()

### 查询条件不是相等

查询年龄大于27岁的用户

    user_list = user_model.where(
        age=('>', 27)
    ).select()

### 复合查询

查询公司为'JDMD'或者年龄大于27岁的用户

    user_list = user_model.where(
        __or={
            'company': 'JDMD',
            'age': ('>', 27)
        }
    ).select()

查询(公司为'JDMD'且年龄大于25岁)或者年龄大于27岁的用户

    user_list = user_model.where(
        __or=(
            {
                'company': 'JDMD',
                'age': ('>', 25)
            },
            {
                'age': ('>', 27)
            }
        )
    ).select()

查询公司为'JDMD'且(年龄大于27岁或者年龄小于23岁)的用户

    user_list = user_model.where(
        company='JDMD',
        __or=(
            {
                'age': ('>', 27),
            },
            {
                'age': ('<', 23),
            }
        )
    ).select()

### 连接查询

    user_list = user_model.join(
        'company',
        {
            'company.name': F('user.company')
        }
    ).select()

join的第一个参数是表名，第二个参数是查询条件。

`F`表示user.company是一个字段，而不是一个字符串。

### 排序查询

    user_list = user_model.order(
        'age', 'DESC'
    ).select()

order的第一个参数是排序的列名，第二个参数是排序顺序

多个排序规则可以调用多次order

    user_list = user_model.order(
        'age', 'DESC'
    ).order(
        'id', 'ASC'
    ).select()

这里没有使用字典的原因是字典读取key的顺序可能与写入时不同

### limit与offset

    user_list = user_model.limit(10).offset(20).select()

此需求常见于分页

### select and count

它的用途的是在select的同时，
查询共有多少条满足条件。

    user_list, user_in_jdmd_count = user_model.where(
        company='JDMD'
    ).limit(10).offset(20).select_and_count()

`select_and_count`会返回两个值。

第一个值和普通的select返回的值一样，
由于limit的限制，
最多可能返回10条记录。

第二个值是符合where条件的记录的总数，
也就是说它的计数包含了where条件，
但是忽略了limit和offset。

在分页的时候，
除了获取当前页的数据外，
还需要计算总共有多少页。
通过`select_and_count`就可以同时得到当前页的数据和总共有多少条。
通过总共有多少条，做个简单的除法，就可以知道总共有多少页。

### group by

    user_list = user_model.join(
        'company',
        {
            'company.name': 'user.company'
        }
    ).group(
        'company.id'
    ).select()
