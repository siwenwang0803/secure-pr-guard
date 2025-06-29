# 测试文件 - 故意包含格式问题供Patch-Agent修复

def test_function():
    # 问题1: 使用Tab缩进而不是空格
    very_long_line_that_exceeds_one_hundred_twenty_characters_and_should_be_split_into_multiple_lines_for_better_readability = (
        "This is a very long string"
    )
    
    # 问题2: 变量名风格不一致
    very_bad_variable_name = "bad style"
    
    return very_long_line_that_exceeds_one_hundred_twenty_characters_and_should_be_split_into_multiple_lines_for_better_readability

# 问题3: 更多的Tab缩进问题
if True:
    print("This line uses tabs instead of spaces")
    for i in range(10):
        print(f"Item {i} - this is another very long line that definitely exceeds the 120 character limit and should be shortened")