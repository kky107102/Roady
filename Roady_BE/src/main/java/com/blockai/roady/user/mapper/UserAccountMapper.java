package com.blockai.roady.user.mapper;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import org.apache.ibatis.annotations.Arg;
import org.apache.ibatis.annotations.ConstructorArgs;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface UserAccountMapper {

    @Select("""
            SELECT
                id,
                username,
                password_hash,
                email,
                name,
                assigned_region_code,
                role,
                active,
                created_at
            FROM users
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "username", javaType = String.class),
            @Arg(column = "password_hash", javaType = String.class),
            @Arg(column = "email", javaType = String.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "assigned_region_code", javaType = String.class),
            @Arg(column = "role", javaType = UserRole.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    UserAccount findById(@Param("id") Long id);

    @Select("""
            SELECT
                id,
                username,
                password_hash,
                email,
                name,
                assigned_region_code,
                role,
                active,
                created_at
            FROM users
            WHERE username = #{username}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "username", javaType = String.class),
            @Arg(column = "password_hash", javaType = String.class),
            @Arg(column = "email", javaType = String.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "assigned_region_code", javaType = String.class),
            @Arg(column = "role", javaType = UserRole.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    UserAccount findByUsername(@Param("username") String username);

    @Select("""
            SELECT
                id,
                username,
                password_hash,
                email,
                name,
                assigned_region_code,
                role,
                active,
                created_at
            FROM users
            ORDER BY created_at ASC, id ASC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "username", javaType = String.class),
            @Arg(column = "password_hash", javaType = String.class),
            @Arg(column = "email", javaType = String.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "assigned_region_code", javaType = String.class),
            @Arg(column = "role", javaType = UserRole.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<UserAccount> findAll();

    @Select("""
            <script>
            SELECT
                id,
                username,
                password_hash,
                email,
                name,
                assigned_region_code,
                role,
                active,
                created_at
            FROM users
            <where>
                <if test="role != null">
                    AND role = #{role}
                </if>
                <if test="active != null">
                    AND active = #{active}
                </if>
            </where>
            ORDER BY created_at ASC, id ASC
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "username", javaType = String.class),
            @Arg(column = "password_hash", javaType = String.class),
            @Arg(column = "email", javaType = String.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "assigned_region_code", javaType = String.class),
            @Arg(column = "role", javaType = UserRole.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<UserAccount> findAllByFilters(
            @Param("role") UserRole role,
            @Param("active") Boolean active
    );

    @Select("SELECT COUNT(*) > 0 FROM users WHERE username = #{username}")
    boolean existsByUsername(@Param("username") String username);

    @Select("SELECT COUNT(*) > 0 FROM users WHERE email = #{email}")
    boolean existsByEmail(@Param("email") String email);

    @Insert("""
            INSERT INTO users (username, password_hash, email, name, role, active)
            VALUES (#{username}, #{passwordHash}, #{email}, #{name}, #{role}, TRUE)
            """)
    int insert(
            @Param("username") String username,
            @Param("passwordHash") String passwordHash,
            @Param("email") String email,
            @Param("name") String name,
            @Param("role") UserRole role
    );

    @Update("""
            UPDATE users
            SET role = #{role}
            WHERE id = #{id}
            """)
    int updateRole(@Param("id") Long id, @Param("role") UserRole role);

    @Update("""
            UPDATE users
            SET active = #{active}
            WHERE id = #{id}
            """)
    int updateActive(@Param("id") Long id, @Param("active") boolean active);

    @Update("""
            UPDATE users
            SET assigned_region_code = #{assignedRegionCode}
            WHERE id = #{id}
            """)
    int updateAssignedRegion(
            @Param("id") Long id,
            @Param("assignedRegionCode") String assignedRegionCode
    );
}
