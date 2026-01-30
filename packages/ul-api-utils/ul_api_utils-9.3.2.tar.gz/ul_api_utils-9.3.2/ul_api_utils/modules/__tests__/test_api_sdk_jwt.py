import json
import sys
from datetime import datetime, time
from typing import List
from uuid import uuid4, UUID

from ul_py_tool.utils.write_stdout import write_stdout

from ul_api_utils.conf import APPLICATION_ENV
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt


def print_score(name: str, compressed: str, uncompressed: str) -> None:
    write_stdout(
        f'\n\n{name} '
        f':: uncompressed={len(uncompressed)} '
        f'({sys.getsizeof(uncompressed)}) '
        f':: compressed={len(compressed)} '
        f'({sys.getsizeof(compressed)}) '
        f':: diff={((len(uncompressed) - len(compressed)) / len(uncompressed)) * 100:0.3f}% '
        f'({((sys.getsizeof(uncompressed) - sys.getsizeof(compressed)) / sys.getsizeof(uncompressed)) * 100:0.3f}%)',
    )


def test_jwt_compressed() -> None:
    att, _rtt = ApiSdkJwt.create_jwt_pair(
        environment='production',
        user_id=UUID('1870e062-7914-4e56-8fe7-dad7b00a67c3'),
        organization_id=UUID("5dca46d3-8fcb-4ce7-856e-f6c0104f3b72"),
        permissions=[13127, 91701, 91702, 91703, 91704, 91705, 90901, 90905, 91801, 91802, 91803, 91804, 91805, 10007, 90301, 13068, 13014, 13017, 13032, 13033, 13034, 13072, 13040, 13041, 13042, 13043, 13044, 13046, 13047, 13048, 13049, 13050, 13052, 13053, 13054, 13055, 13056, 13057, 13058, 13059, 13060, 13061, 13062, 13064, 91401, 91402, 13065, 13066, 91403, 91404, 91405, 91406, 10001, 13067, 13069, 13076, 13077, 10005, 13070, 13071, 90902, 90903, 90904, 90906, 10013, 90907, 90908, 90909, 90401, 90402, 90403, 90404, 90405, 90406, 90407, 90408, 13083, 13084, 13085, 13091, 10021, 10023, 13086, 10025, 13097, 10034, 13098, 13087, 10029, 10031, 10033, 13105, 13106, 13088, 10036, 10037, 10039, 10040, 13089, 13113, 13112, 13114, 13115, 13090, 13116, 13122, 13118, 13119, 13120, 13121, 13125, 13132, 13124, 13126, 13092, 13128, 13129, 13130, 13131, 13093, 13133, 13134, 10041, 13094, 13095, 13080, 13096, 91501, 91502, 91503, 91504, 13099, 91505, 91506, 13100, 91001, 13081, 13101, 13102, 13103, 90501, 90502, 90503, 90504, 13104, 90505, 90506, 90507, 90508, 90001, 90002, 90003, 13082, 13107, 13108, 13109, 13110, 13111, 13117, 91601, 91602, 91603, 91604, 91605, 90101, 90102, 90103, 90104, 90105, 90106, 90107, 90108, 90109, 90110, 90111],  # noqa: E501
    )

    for algo in ['RS256', 'ES256']:
        priv_k, pub_k_fn = ApiSdkJwt.generate_cert(algo)  # type: ignore
        pub_key = pub_k_fn()

        uncompressed = att.encode(priv_k, algo)  # type: ignore
        compressed = att.encode(priv_k, algo, compressed=True)  # type: ignore

        print_score(algo, compressed, uncompressed)

        t_decoded_uncompressed = ApiSdkJwt.decode(uncompressed, pub_key)._asdict()
        t_decoded_compressed = ApiSdkJwt.decode(compressed, pub_key)._asdict()

        t_decoded_uncompressed.pop('raw')
        t_decoded_compressed.pop('raw')

        t_decoded_uncompressed['exp_date'] = datetime.combine(
            t_decoded_uncompressed['exp_date'].date(),
            time(
                hour=t_decoded_uncompressed['exp_date'].time().hour,
                minute=t_decoded_uncompressed['exp_date'].time().minute,
            ),
        )

        assert t_decoded_uncompressed == t_decoded_compressed


def test_jwt_cert() -> None:
    for algo in ['RS256', 'ES256']:
        pk1, pkf1 = ApiSdkJwt.generate_cert(algo)  # type: ignore

        pk2, pkf2 = ApiSdkJwt.load_cert(pk1)

        att, rtt = ApiSdkJwt.create_jwt_pair(
            environment=APPLICATION_ENV,
            user_id=uuid4(),
            organization_id=uuid4(),
            permissions=[],
        )
        at, *_ = att.encode(pk1, algo), rtt.encode(pk1, algo)  # type: ignore

        assert ApiSdkJwt.decode(at, pkf1()) == ApiSdkJwt.decode(at, pkf2())

        assert pk1 == pk2

    for algo1, algo2 in [('RS256', 'ES256'), ('ES256', 'RS256')]:
        pk1, _pkf1 = ApiSdkJwt.generate_cert(algo1)  # type: ignore

        att, _rtt = ApiSdkJwt.create_jwt_pair(
            environment=APPLICATION_ENV,
            user_id=uuid4(),
            organization_id=uuid4(),
            permissions=[],
        )

        try:
            att.encode(pk1, algo2)  # type: ignore
        except Exception:  # noqa: B902
            pass
        else:
            raise AssertionError()


def test_jwt() -> None:
    for algo in ['RS256', 'ES256']:
        private_key, public_key_factory = ApiSdkJwt.generate_cert(algo)  # type: ignore
        att, rtt = ApiSdkJwt.create_jwt_pair(
            environment=APPLICATION_ENV,
            user_id=uuid4(),
            organization_id=uuid4(),
            permissions=[13127, 91701, 91702, 91703, 91704, 91705, 90901, 90905, 91801, 91802, 91803, 91804, 91805, 10007, 90301, 13068, 13014, 13017, 13032, 13033, 13034, 13072, 13040, 13041, 13042, 13043, 13044, 13046, 13047, 13048, 13049, 13050, 13052, 13053, 13054, 13055, 13056, 13057, 13058, 13059, 13060, 13061, 13062, 13064, 91401, 91402, 13065, 13066, 91403, 91404, 91405, 91406, 10001, 13067, 13069, 13076, 13077, 10005, 13070, 13071, 90902, 90903, 90904, 90906, 10013, 90907, 90908, 90909, 90401, 90402, 90403, 90404, 90405, 90406, 90407, 90408, 13083, 13084, 13085, 13091, 10021, 10023, 13086, 10025, 13097, 10034, 13098, 13087, 10029, 10031, 10033, 13105, 13106, 13088, 10036, 10037, 10039, 10040, 13089, 13113, 13112, 13114, 13115, 13090, 13116, 13122, 13118, 13119, 13120, 13121, 13125, 13132, 13124, 13126, 13092, 13128, 13129, 13130, 13131, 13093, 13133, 13134, 10041, 13094, 13095, 13080, 13096, 91501, 91502, 91503, 91504, 13099, 91505, 91506, 13100, 91001, 13081, 13101, 13102, 13103, 90501, 90502, 90503, 90504, 13104, 90505, 90506, 90507, 90508, 90001, 90002, 90003, 13082, 13107, 13108, 13109, 13110, 13111, 13117, 91601, 91602, 91603, 91604, 91605, 90101, 90102, 90103, 90104, 90105, 90106, 90107, 90108, 90109, 90110, 90111],  # noqa: E501,
        )

        at, rt = att.encode(private_key, algo), rtt.encode(private_key, algo)  # type: ignore

        parsed_at = ApiSdkJwt.decode(at, public_key_factory())

        assert att.env == parsed_at.env == APPLICATION_ENV
        assert att.id == parsed_at.id
        assert att.user_id == parsed_at.user_id
        assert att.organization_id == parsed_at.organization_id
        assert att.version == parsed_at.version
        assert att.token_type == parsed_at.token_type
        assert att.exp_date == parsed_at.exp_date
        assert att.permissions == parsed_at.permissions
        assert att.additional_data == parsed_at.additional_data

        new_at = ApiSdkJwt.decode(rt, public_key_factory()).create_access_token().encode(private_key, algo, True)  # type: ignore

        parsed_t = ApiSdkJwt.decode(token=new_at, username=None, certificate=public_key_factory())

        assert parsed_t.env == rtt.env == APPLICATION_ENV
        assert parsed_t.id == rtt.id
        assert parsed_t.user_id == rtt.user_id
        assert parsed_t.organization_id == rtt.organization_id
        assert parsed_t.version == rtt.version
        assert parsed_t.token_type == 'access'
        assert parsed_t.exp_date <= rtt.exp_date
        assert parsed_t.permissions == rtt.permissions
        assert parsed_t.additional_data == rtt.additional_data


# opts: [5] => [1111011, 11110000011110011]


def test_permission_compression() -> None:
    c_permissions = ApiSdkJwt.compress_permissions([1, 2, 5, 3, 4])
    assert c_permissions == '%1'


def test_permission_decompression() -> None:
    c_permissions = ApiSdkJwt.decompress_permissions('A5')
    assert c_permissions == [1, 2, 3, 4, 5]


def test_permission_compression_decompression() -> None:
    permissions = [13127, 91701, 91702, 91703, 91704, 91705, 90901, 90905, 91801, 91802, 91803, 91804, 91805, 10007, 90301, 13068, 13014, 13017, 13032, 13033, 13034, 13072, 13040, 13041, 13042, 13043, 13044, 13046, 13047, 13048, 13049, 13050, 13052, 13053, 13054, 13055, 13056, 13057, 13058, 13059, 13060, 13061, 13062, 13064, 91401, 91402, 13065, 13066, 91403, 91404, 91405, 91406, 10001, 13067, 13069, 13076, 13077, 10005, 13070, 13071, 90902, 90903, 90904, 90906, 10013, 90907, 90908, 90909, 90401, 90402, 90403, 90404, 90405, 90406, 90407, 90408, 13083, 13084, 13085, 13091, 10021, 10023, 13086, 10025, 13097, 10034, 13098, 13087, 10029, 10031, 10033, 13105, 13106, 13088, 10036, 10037, 10039, 10040, 13089, 13113, 13112, 13114, 13115, 13090, 13116, 13122, 13118, 13119, 13120, 13121, 13125, 13132, 13124, 13126, 13092, 13128, 13129, 13130, 13131, 13093, 13133, 13134, 10041, 13094, 13095, 13080, 13096, 91501, 91502, 91503, 91504, 13099, 91505, 91506, 13100, 91001, 13081, 13101, 13102, 13103, 90501, 90502, 90503, 90504, 13104, 90505, 90506, 90507, 90508, 90001, 90002, 90003, 13082, 13107, 13108, 13109, 13110, 13111, 13117, 91601, 91602, 91603, 91604, 91605, 90101, 90102, 90103, 90104, 90105, 90106, 90107, 90108, 90109, 90110, 90111]  # noqa: E501
    p_permissions = list(sorted(set(permissions)))
    c_permissions = ApiSdkJwt.compress_permissions(permissions)
    assert p_permissions == ApiSdkJwt.decompress_permissions(c_permissions)

    r_p = json.dumps(p_permissions, separators=(',', ':'))
    r_c = json.dumps(c_permissions, separators=(',', ':'))

    print_score('', r_c, r_p)
    write_stdout(c_permissions)


def test_permission_compression_decompression2() -> None:
    compressed_win = 0
    total_len = 0
    for step in range(1, 999):
        for i in range(0, 100):
            permissions = list(range(999, 999 + step * i, step))
            p_permissions = list(sorted(set(permissions)))
            c_permissions = ApiSdkJwt.compress_permissions(permissions)

            p_l = len(json.dumps(p_permissions, separators=(',', ':')))
            total_len += p_l
            compressed_win += p_l - len(json.dumps(c_permissions, separators=(',', ':')))
            assert p_permissions == ApiSdkJwt.decompress_permissions(c_permissions), f'{i}::{step}::{c_permissions}'

    write_stdout(f'compressed_win={compressed_win}  total_len={total_len}   {compressed_win * 100 / total_len:0.3f}%')


def test_permission_compression_decompression4() -> None:
    import random
    r = random.Random()
    r.seed("test")

    permissions: List[int] = []
    for j in range(1, 501, 20):
        for _i in range(10000):
            v = r.randint(1, j)
            permissions.append(v if not permissions else permissions[-1] + v)

    p_permissions = list(sorted(set(permissions)))
    c_permissions = ApiSdkJwt.compress_permissions(permissions)
    assert p_permissions == ApiSdkJwt.decompress_permissions(c_permissions), c_permissions

    r_p = json.dumps(p_permissions, separators=(',', ':'))
    r_c = json.dumps(c_permissions, separators=(',', ':'))

    print_score('', r_c, r_p)
