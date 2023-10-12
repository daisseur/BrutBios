/**
 * Author......: See docs/credits.txt
 * License.....: MIT
 */

#define NEW_SIMD_CODE

#ifdef KERNEL_STATIC
#include M2S(INCLUDE_PATH/inc_vendor.h)
#include M2S(INCLUDE_PATH/inc_types.h)
#include M2S(INCLUDE_PATH/inc_platform.cl)
#include M2S(INCLUDE_PATH/inc_common.cl)
#include M2S(INCLUDE_PATH/inc_simd.cl)
#include M2S(INCLUDE_PATH/inc_hash_md5.cl)
#endif

#if   VECT_SIZE == 1
#define uint_to_hex_lower8(i) make_u32x (l_bin2asc[(i)])
#elif VECT_SIZE == 2
#define uint_to_hex_lower8(i) make_u32x (l_bin2asc[(i).s0], l_bin2asc[(i).s1])
#elif VECT_SIZE == 4
#define uint_to_hex_lower8(i) make_u32x (l_bin2asc[(i).s0], l_bin2asc[(i).s1], l_bin2asc[(i).s2], l_bin2asc[(i).s3])
#elif VECT_SIZE == 8
#define uint_to_hex_lower8(i) make_u32x (l_bin2asc[(i).s0], l_bin2asc[(i).s1], l_bin2asc[(i).s2], l_bin2asc[(i).s3], l_bin2asc[(i).s4], l_bin2asc[(i).s5], l_bin2asc[(i).s6], l_bin2asc[(i).s7])
#elif VECT_SIZE == 16
#define uint_to_hex_lower8(i) make_u32x (l_bin2asc[(i).s0], l_bin2asc[(i).s1], l_bin2asc[(i).s2], l_bin2asc[(i).s3], l_bin2asc[(i).s4], l_bin2asc[(i).s5], l_bin2asc[(i).s6], l_bin2asc[(i).s7], l_bin2asc[(i).s8], l_bin2asc[(i).s9], l_bin2asc[(i).sa], l_bin2asc[(i).sb], l_bin2asc[(i).sc], l_bin2asc[(i).sd], l_bin2asc[(i).se], l_bin2asc[(i).sf])
#endif

KERNEL_FQ void m21200_mxx (KERN_ATTR_VECTOR ())
{
  /**
   * modifier
   */

  const u64 gid = get_global_id (0);
  const u64 lid = get_local_id (0);
  const u64 lsz = get_local_size (0);

  /**
   * bin2asc table
   */

  LOCAL_VK u32 l_bin2asc[256];

  for (u32 i = lid; i < 256; i += lsz)
  {
    const u32 i0 = (i >> 0) & 15;
    const u32 i1 = (i >> 4) & 15;

    l_bin2asc[i] = ((i0 < 10) ? '0' + i0 : 'a' - 10 + i0) << 8
                 | ((i1 < 10) ? '0' + i1 : 'a' - 10 + i1) << 0;
  }

  SYNC_THREADS ();

  if (gid >= GID_CNT) return;

  /**
   * base
   */

  const u32 pw_len = pws[gid].pw_len;

  u32x w[64] = { 0 };

  for (u32 i = 0, idx = 0; i < pw_len; i += 4, idx += 1)
  {
    w[idx] = pws[gid].i[idx];
  }

  /**
   * salt
   */

  u32x salt_buf0[4];
  u32x salt_buf1[4];
  u32x salt_buf2[4];
  u32x salt_buf3[4];

  salt_buf0[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[0];
  salt_buf0[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[1];
  salt_buf0[2] = salt_bufs[SALT_POS_HOST].salt_buf_pc[2];
  salt_buf0[3] = salt_bufs[SALT_POS_HOST].salt_buf_pc[3];
  salt_buf1[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[4];
  salt_buf1[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[5];
  salt_buf1[2] = salt_bufs[SALT_POS_HOST].salt_buf_pc[6];
  salt_buf1[3] = salt_bufs[SALT_POS_HOST].salt_buf_pc[7];
  salt_buf2[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[8];
  salt_buf2[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[9];
  salt_buf2[2] = 0;
  salt_buf2[3] = 0;
  salt_buf3[0] = 0;
  salt_buf3[1] = 0;
  salt_buf3[2] = 0;
  salt_buf3[3] = 0;

  md5_ctx_vector_t ctx0;

  md5_init_vector (&ctx0);

  md5_update_vector_64 (&ctx0, salt_buf0, salt_buf1, salt_buf2, salt_buf3, 40);

  /**
   * loop
   */

  u32x w0l = w[0];

  for (u32 il_pos = 0; il_pos < IL_CNT; il_pos += VECT_SIZE)
  {
    const u32x w0r = words_buf_r[il_pos / VECT_SIZE];

    const u32x w0 = w0l | w0r;

    w[0] = w0;

    md5_ctx_vector_t ctx1;

    md5_init_vector   (&ctx1);
    md5_update_vector (&ctx1, w, pw_len);
    md5_final_vector  (&ctx1);

    const u32x a = hc_swap32 (ctx1.h[0]);
    const u32x b = hc_swap32 (ctx1.h[1]);
    const u32x c = hc_swap32 (ctx1.h[2]);
    const u32x d = hc_swap32 (ctx1.h[3]);

    // add md5_hex ($pass) to ctx0:

    u32x w0_t[4];
    u32x w1_t[4];
    u32x w2_t[4];
    u32x w3_t[4];

    w0_t[0] = uint_to_hex_lower8 ((a >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((a >> 16) & 255) << 16;
    w0_t[1] = uint_to_hex_lower8 ((a >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((a >>  0) & 255) << 16;
    w0_t[2] = uint_to_hex_lower8 ((b >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((b >> 16) & 255) << 16;
    w0_t[3] = uint_to_hex_lower8 ((b >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((b >>  0) & 255) << 16;
    w1_t[0] = uint_to_hex_lower8 ((c >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((c >> 16) & 255) << 16;
    w1_t[1] = uint_to_hex_lower8 ((c >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((c >>  0) & 255) << 16;
    w1_t[2] = uint_to_hex_lower8 ((d >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((d >> 16) & 255) << 16;
    w1_t[3] = uint_to_hex_lower8 ((d >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((d >>  0) & 255) << 16;

    w2_t[0] = 0;
    w2_t[1] = 0;
    w2_t[2] = 0;
    w2_t[3] = 0;
    w3_t[0] = 0;
    w3_t[1] = 0;
    w3_t[2] = 0;
    w3_t[3] = 0;

    md5_ctx_vector_t ctx = ctx0;

    md5_update_vector_64 (&ctx, w0_t, w1_t, w2_t, w3_t, 32);

    md5_final_vector (&ctx);

    const u32x r0 = ctx.h[DGST_R0];
    const u32x r1 = ctx.h[DGST_R1];
    const u32x r2 = ctx.h[DGST_R2];
    const u32x r3 = ctx.h[DGST_R3];

    COMPARE_M_SIMD (r0, r1, r2, r3);
  }
}

KERNEL_FQ void m21200_sxx (KERN_ATTR_VECTOR ())
{
  /**
   * modifier
   */

  const u64 gid = get_global_id (0);
  const u64 lid = get_local_id (0);
  const u64 lsz = get_local_size (0);

  /**
   * bin2asc table
   */

  LOCAL_VK u32 l_bin2asc[256];

  for (u32 i = lid; i < 256; i += lsz)
  {
    const u32 i0 = (i >> 0) & 15;
    const u32 i1 = (i >> 4) & 15;

    l_bin2asc[i] = ((i0 < 10) ? '0' + i0 : 'a' - 10 + i0) << 8
                 | ((i1 < 10) ? '0' + i1 : 'a' - 10 + i1) << 0;
  }

  SYNC_THREADS ();

  if (gid >= GID_CNT) return;

  /**
   * digest
   */

  const u32 search[4] =
  {
    digests_buf[DIGESTS_OFFSET_HOST].digest_buf[DGST_R0],
    digests_buf[DIGESTS_OFFSET_HOST].digest_buf[DGST_R1],
    digests_buf[DIGESTS_OFFSET_HOST].digest_buf[DGST_R2],
    digests_buf[DIGESTS_OFFSET_HOST].digest_buf[DGST_R3]
  };

  /**
   * base
   */

  const u32 pw_len = pws[gid].pw_len;

  u32x w[64] = { 0 };

  for (u32 i = 0, idx = 0; i < pw_len; i += 4, idx += 1)
  {
    w[idx] = pws[gid].i[idx];
  }

  /**
   * salt
   */

  u32x salt_buf0[4];
  u32x salt_buf1[4];
  u32x salt_buf2[4];
  u32x salt_buf3[4];

  salt_buf0[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[0];
  salt_buf0[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[1];
  salt_buf0[2] = salt_bufs[SALT_POS_HOST].salt_buf_pc[2];
  salt_buf0[3] = salt_bufs[SALT_POS_HOST].salt_buf_pc[3];
  salt_buf1[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[4];
  salt_buf1[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[5];
  salt_buf1[2] = salt_bufs[SALT_POS_HOST].salt_buf_pc[6];
  salt_buf1[3] = salt_bufs[SALT_POS_HOST].salt_buf_pc[7];
  salt_buf2[0] = salt_bufs[SALT_POS_HOST].salt_buf_pc[8];
  salt_buf2[1] = salt_bufs[SALT_POS_HOST].salt_buf_pc[9];
  salt_buf2[2] = 0;
  salt_buf2[3] = 0;
  salt_buf3[0] = 0;
  salt_buf3[1] = 0;
  salt_buf3[2] = 0;
  salt_buf3[3] = 0;

  md5_ctx_vector_t ctx0;

  md5_init_vector (&ctx0);

  md5_update_vector_64 (&ctx0, salt_buf0, salt_buf1, salt_buf2, salt_buf3, 40);

  /**
   * loop
   */

  u32x w0l = w[0];

  for (u32 il_pos = 0; il_pos < IL_CNT; il_pos += VECT_SIZE)
  {
    const u32x w0r = words_buf_r[il_pos / VECT_SIZE];

    const u32x w0 = w0l | w0r;

    w[0] = w0;

    md5_ctx_vector_t ctx1;

    md5_init_vector   (&ctx1);
    md5_update_vector (&ctx1, w, pw_len);
    md5_final_vector  (&ctx1);

    const u32x a = hc_swap32 (ctx1.h[0]);
    const u32x b = hc_swap32 (ctx1.h[1]);
    const u32x c = hc_swap32 (ctx1.h[2]);
    const u32x d = hc_swap32 (ctx1.h[3]);

    // add md5_hex ($pass) to ctx0:

    u32x w0_t[4];
    u32x w1_t[4];
    u32x w2_t[4];
    u32x w3_t[4];

    w0_t[0] = uint_to_hex_lower8 ((a >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((a >> 16) & 255) << 16;
    w0_t[1] = uint_to_hex_lower8 ((a >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((a >>  0) & 255) << 16;
    w0_t[2] = uint_to_hex_lower8 ((b >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((b >> 16) & 255) << 16;
    w0_t[3] = uint_to_hex_lower8 ((b >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((b >>  0) & 255) << 16;
    w1_t[0] = uint_to_hex_lower8 ((c >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((c >> 16) & 255) << 16;
    w1_t[1] = uint_to_hex_lower8 ((c >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((c >>  0) & 255) << 16;
    w1_t[2] = uint_to_hex_lower8 ((d >> 24) & 255) <<  0
            | uint_to_hex_lower8 ((d >> 16) & 255) << 16;
    w1_t[3] = uint_to_hex_lower8 ((d >>  8) & 255) <<  0
            | uint_to_hex_lower8 ((d >>  0) & 255) << 16;

    w2_t[0] = 0;
    w2_t[1] = 0;
    w2_t[2] = 0;
    w2_t[3] = 0;
    w3_t[0] = 0;
    w3_t[1] = 0;
    w3_t[2] = 0;
    w3_t[3] = 0;

    md5_ctx_vector_t ctx = ctx0;

    md5_update_vector_64 (&ctx, w0_t, w1_t, w2_t, w3_t, 32);

    md5_final_vector (&ctx);

    const u32x r0 = ctx.h[DGST_R0];
    const u32x r1 = ctx.h[DGST_R1];
    const u32x r2 = ctx.h[DGST_R2];
    const u32x r3 = ctx.h[DGST_R3];

    COMPARE_S_SIMD (r0, r1, r2, r3);
  }
}
